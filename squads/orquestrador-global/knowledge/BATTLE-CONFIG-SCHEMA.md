# Battle Configuration Schema

## Overview

Este documento define o schema de configuração para Battles (Pattern 6: Battle Royale) no Mega Brain Agent Teams. Cada squad que adotar o Battle pattern DEVE incluir uma seção `battle` no seu `squad.yaml` ou em um arquivo de configuração dedicado (`battle-config.yaml`).

O schema define 4 seções principais:

| Seção | Propósito |
|-------|-----------|
| `teams` | Divisão de agentes em equipes competidoras |
| `scoring` | Critérios e pesos para votação cruzada |
| `debate` | Formato e regras do debate estruturado |
| `board` | Composição e gate de aprovação do board de revisão |

**Referências:**
- Pattern: `TEAM-PATTERNS.md#pattern-6-battle-royale`
- Workflow: `workflows/battle-round.md`
- PRD: `docs/prd-battle-system.md` (FR2, FR4, FR6, FR8, FR10, FR14)

---

## Schema Specification

### 1. Teams

Define como os agentes do squad são divididos em equipes competidoras.

```yaml
battle:
  teams:
    count: 3                        # Obrigatório: número de equipes (2–4)
    agents_per_team: 3              # Obrigatório: agentes por equipe (mínimo 2)
    team_definitions:               # Obrigatório: array com cada equipe
      - id: team-a                  # Obrigatório: identificador único (kebab-case)
        name: "Nome da Equipe"      # Obrigatório: nome descritivo para logs
        leader: agent-id            # Obrigatório: quem vota e debate (Defensor/Desafiante)
        members: [agent-id, ...]    # Obrigatório: lista de agentes da equipe (inclui líder)
        angle: "descrição"          # Opcional: perspectiva/ângulo da equipe
    reserve_agents: []              # Opcional: agentes de reserva se um falhar
```

**Regras de validação:**
- `count` deve ser entre 2 e 4. Configurações com 4 equipes são experimentais (REC-02)
- `agents_per_team` mínimo 2 (líder + pelo menos 1 membro)
- Total de agentes (`count × agents_per_team + reserve`) ≤ 17. Warning acima de 13 agentes
- O `leader` DEVE estar incluído na lista `members`
- Cada `id` DEVE ser único dentro do Battle
- Agentes designados como `board.reviewers` NÃO PODEM aparecer em nenhum `members` (FR8.1)

### 2. Scoring

Define os critérios de votação cruzada e seus pesos.

```yaml
battle:
  scoring:
    criteria_file: "knowledge/BATTLE-SCORING-CRITERIA.md"  # Obrigatório: path para arquivo com rubrica detalhada
    criteria:                       # Obrigatório: mínimo 3, máximo 10 critérios
      - id: criterion-id            # Obrigatório: identificador snake_case
        name: "Nome do Critério"    # Obrigatório: nome para exibição
        weight: 0.15                # Obrigatório: float entre 0.01 e 1.0
        scale: 1-10                 # Fixo: escala de avaliação
        description: ""             # Opcional: resumo (rubrica detalhada no criteria_file)
    weights_must_sum_to: 1.0        # Regra de validação (informativo)
    auto_vote_prohibition: true     # Fixo: proibido votar na própria equipe
    voters: leaders_only            # Opções: leaders_only (padrão) | all_members
```

**Regras de validação:**
- A soma de todos os `weight` DEVE ser exatamente `1.0` (tolerância: ±0.001)
- Mínimo 3 critérios, máximo 10
- `criteria_file` DEVE apontar para um arquivo `.md` existente com rubrica 1-10 para cada critério (FR10)
- `voters: leaders_only` é o padrão recomendado (REC-03) — simplifica de N×M para N scorecards

### 3. Debate

Define o formato do debate estruturado entre as top 2 equipes.

```yaml
battle:
  debate:
    rounds: 3                       # Padrão: 3 rodadas
    round_definitions:              # Opcional: sobrescrever nomes e limites
      - name: "Apresentação"        # Rodada 1: cada lado apresenta sua peça
        max_words: 200
        role: "ambos"               # ambos os lados falam
      - name: "Ataque"             # Rodada 2: cada lado ataca os pontos fracos do oponente
        max_words: 200
        role: "ambos"
      - name: "Síntese"           # Rodada 3: cada lado sintetiza e defende
        max_words: 300
        role: "ambos"
    tiebreaker_round: true          # Opcional: rodada extra se placar ≤5% diferença
    judge_role: chief               # Fixo: chief é sempre o juiz
    relay_mode: true                # Fixo: toda comunicação passa pelo chief (ADR-003)
```

**Regras de validação:**
- `rounds` mínimo 2, máximo 5 (padrão 3)
- `max_words` é informativo — o chief inclui o limite no prompt de cada rodada
- `relay_mode` é sempre `true` — líderes NÃO se comunicam diretamente (ADR-003)
- `judge_role` é sempre `chief` — não pode ser delegado a outro agente

### 4. Board

Define a composição e regras do board de revisão final.

```yaml
battle:
  board:
    reviewers:                      # Obrigatório: mínimo 2, máximo 5 revisores
      - agent: agent-id             # Obrigatório: ID do agente revisor
        framework: "Nome"           # Obrigatório: framework de revisão que usa
        vote_weight: 1              # Opcional: peso do voto (padrão 1)
    approval_gate: unanimous        # Opções: unanimous (padrão) | majority
    max_rounds: 3                   # Padrão: máximo de rodadas de revisão
    escalation:
      after_max_rounds: human       # O que fazer se reprovado N vezes: human | force_approve
```

**Regras de validação:**
- Mínimo 2 revisores, máximo 5
- Nenhum `agent` em `reviewers` pode ser membro de qualquer equipe em `teams.team_definitions` (FR8.1)
- `approval_gate: unanimous` significa TODOS devem votar APROVADO
- `approval_gate: majority` significa >50% devem votar APROVADO (arredondado para cima)
- `max_rounds` mínimo 1, máximo 5 (padrão 3)
- `escalation.after_max_rounds: human` pausa e notifica o usuário para decisão manual

---

## Model Strategy

Recomendação de modelo por papel no Battle (FR14):

```yaml
battle:
  model_strategy:
    chief: opus              # Análise de brief, moderação do debate, veredito
    judge: opus              # Mesmo que chief (chief é o juiz)
    board: opus              # Revisores do board (alta precisão requerida)
    producers: sonnet        # Agentes que produzem os deliverables
    voters: sonnet           # Líderes que avaliam/pontuam
    support: haiku           # Tarefas auxiliares (formatação, compilação)
```

**Nota:** O campo `judge` e `chief` apontam para o mesmo agente — estão separados para clareza semântica. Na prática, o chief assume o papel de juiz na Fase 4.

---

## Field Reference Table

| Campo | Tipo | Obrigatório | Padrão | Validação |
|-------|------|-------------|--------|-----------|
| `teams.count` | integer | Sim | — | 2–4 |
| `teams.agents_per_team` | integer | Sim | — | mín. 2 |
| `teams.team_definitions` | array | Sim | — | length = teams.count |
| `teams.team_definitions[].id` | string | Sim | — | kebab-case, único |
| `teams.team_definitions[].name` | string | Sim | — | — |
| `teams.team_definitions[].leader` | string | Sim | — | deve estar em members |
| `teams.team_definitions[].members` | array | Sim | — | inclui líder |
| `teams.team_definitions[].angle` | string | Não | — | — |
| `teams.reserve_agents` | array | Não | `[]` | — |
| `scoring.criteria_file` | string | Sim | — | path para .md existente |
| `scoring.criteria` | array | Sim | — | mín. 3, máx. 10 itens |
| `scoring.criteria[].id` | string | Sim | — | snake_case |
| `scoring.criteria[].name` | string | Sim | — | — |
| `scoring.criteria[].weight` | float | Sim | — | 0.01–1.0; soma = 1.0 |
| `scoring.criteria[].scale` | string | Fixo | `1-10` | imutável |
| `scoring.criteria[].description` | string | Não | — | — |
| `scoring.auto_vote_prohibition` | boolean | Fixo | `true` | imutável |
| `scoring.voters` | string | Não | `leaders_only` | leaders_only \| all_members |
| `debate.rounds` | integer | Não | `3` | 2–5 |
| `debate.round_definitions` | array | Não | (ver padrão) | length = debate.rounds |
| `debate.round_definitions[].name` | string | Sim | — | — |
| `debate.round_definitions[].max_words` | integer | Sim | — | mín. 50, máx. 1000 |
| `debate.round_definitions[].role` | string | Sim | `ambos` | ambos \| defensor \| desafiante |
| `debate.tiebreaker_round` | boolean | Não | `true` | — |
| `debate.judge_role` | string | Fixo | `chief` | imutável |
| `debate.relay_mode` | boolean | Fixo | `true` | imutável (ADR-003) |
| `board.reviewers` | array | Sim | — | mín. 2, máx. 5 |
| `board.reviewers[].agent` | string | Sim | — | não pode ser membro de equipe |
| `board.reviewers[].framework` | string | Sim | — | — |
| `board.reviewers[].vote_weight` | integer | Não | `1` | mín. 1 |
| `board.approval_gate` | string | Não | `unanimous` | unanimous \| majority |
| `board.max_rounds` | integer | Não | `3` | 1–5 |
| `board.escalation.after_max_rounds` | string | Não | `human` | human \| force_approve |
| `model_strategy.chief` | string | Não | `opus` | opus \| sonnet \| haiku |
| `model_strategy.judge` | string | Não | `opus` | opus \| sonnet \| haiku |
| `model_strategy.board` | string | Não | `opus` | opus \| sonnet \| haiku |
| `model_strategy.producers` | string | Não | `sonnet` | opus \| sonnet \| haiku |
| `model_strategy.voters` | string | Não | `sonnet` | opus \| sonnet \| haiku |
| `model_strategy.support` | string | Não | `haiku` | opus \| sonnet \| haiku |

---

## Example 1 — Copywriting (Carta de Vendas)

Primeiro squad a adotar o Battle pattern (FR13). 3 equipes de 3 copywriters, divididas por ângulo persuasivo.

```yaml
battle:
  teams:
    count: 3
    agents_per_team: 3
    team_definitions:
      - id: team-emotional
        name: "Equipe Emocional"
        leader: gary-halbert
        members: [gary-halbert, clayton-makepeace, joe-sugarman]
        angle: "Emocional — dor, desejo, transformação pessoal"
      - id: team-mechanism
        name: "Equipe Mecanismo"
        leader: stefan-georgi
        members: [stefan-georgi, todd-brown, eugene-schwartz]
        angle: "Mecanismo — RMBC, Big Idea, Unique Mechanism"
      - id: team-urgency
        name: "Equipe Urgência"
        leader: dan-kennedy
        members: [dan-kennedy, claude-hopkins, victor-schwab]
        angle: "Urgência — escassez, prova científica, AIDA"
    reserve_agents: [jason-fladlien, jon-benson, robert-bly]

  scoring:
    criteria_file: "knowledge/BATTLE-SCORING-CRITERIA.md"
    criteria:
      - id: headline_power
        name: "Headline Power"
        weight: 0.15
        description: "Impacto e curiosidade do headline principal"
      - id: hook_lead
        name: "Hook / Lead"
        weight: 0.15
        description: "Capacidade de prender nos primeiros 3 parágrafos"
      - id: mechanism_big_idea
        name: "Mechanism / Big Idea"
        weight: 0.12
        description: "Clareza e originalidade do mecanismo único"
      - id: proof_elements
        name: "Proof Elements"
        weight: 0.10
        description: "Qualidade e quantidade de provas e depoimentos"
      - id: emotional_resonance
        name: "Emotional Resonance"
        weight: 0.12
        description: "Conexão emocional com o avatar"
      - id: clarity_flow
        name: "Clarity & Flow"
        weight: 0.10
        description: "Clareza de escrita e fluxo de leitura"
      - id: cta_strength
        name: "CTA Strength"
        weight: 0.10
        description: "Força e clareza da chamada para ação"
      - id: unique_mechanism
        name: "Unique Mechanism"
        weight: 0.08
        description: "Diferenciação do mecanismo vs concorrência"
      - id: objection_handling
        name: "Objection Handling"
        weight: 0.08
        description: "Cobertura e eficácia no tratamento de objeções"
    # Soma: 0.15+0.15+0.12+0.10+0.12+0.10+0.10+0.08+0.08 = 1.00
    auto_vote_prohibition: true
    voters: leaders_only

  debate:
    rounds: 3
    round_definitions:
      - name: "Apresentação"
        max_words: 200
        role: "ambos"
      - name: "Ataque"
        max_words: 200
        role: "ambos"
      - name: "Síntese"
        max_words: 300
        role: "ambos"
    tiebreaker_round: true
    judge_role: chief
    relay_mode: true

  board:
    reviewers:
      - agent: david-ogilvy
        framework: "Big Idea Evaluation"
        vote_weight: 1
      - agent: john-caples
        framework: "Tested Advertising Methods"
        vote_weight: 1
      - agent: gary-bencivenga
        framework: "Persuasion Equation"
        vote_weight: 1
    approval_gate: unanimous
    max_rounds: 3
    escalation:
      after_max_rounds: human

  model_strategy:
    chief: opus
    judge: opus
    board: opus
    producers: sonnet
    voters: sonnet
    support: haiku
```

**Validação:**
- Pesos somam: 0.15 + 0.15 + 0.12 + 0.10 + 0.12 + 0.10 + 0.10 + 0.08 + 0.08 = **1.00**
- Board (ogilvy, caples, bencivenga) não aparecem em nenhuma equipe
- Total de agentes: 9 produtores + 2 reservas = 11 (< 13, sem warning)
- 9 critérios (entre 3 e 10)

---

## Example 2 — Creative Studio (Criativos Visuais)

3 equipes de designers competindo por criativos para Meta Ads.

```yaml
battle:
  teams:
    count: 3
    agents_per_team: 2
    team_definitions:
      - id: team-ugc
        name: "Equipe UGC Nativo"
        leader: dara-denney
        members: [dara-denney, social-media-creator]
        angle: "UGC nativo — storytelling, hooks, formatos orgânicos"
      - id: team-performance
        name: "Equipe Performance"
        leader: andrew-foxwell
        members: [andrew-foxwell, meta-ads-creator]
        angle: "Performance — testes A/B, formatos validados, CTR máximo"
      - id: team-prompt
        name: "Equipe AI-First"
        leader: prompt-engineer
        members: [prompt-engineer, google-ads-creator]
        angle: "AI-First — prompts avançados, Imagen 3, inovação visual"
    reserve_agents: []

  scoring:
    criteria_file: "knowledge/BATTLE-SCORING-CRITERIA-VISUAL.md"
    criteria:
      - id: visual_impact
        name: "Visual Impact"
        weight: 0.20
        description: "Impacto visual nos primeiros 2 segundos (thumb-stop)"
      - id: message_clarity
        name: "Message Clarity"
        weight: 0.20
        description: "Clareza da mensagem principal sem ler o texto"
      - id: brand_consistency
        name: "Brand Consistency"
        weight: 0.15
        description: "Alinhamento com identidade visual da marca"
      - id: cta_visibility
        name: "CTA Visibility"
        weight: 0.15
        description: "Visibilidade e clareza do call-to-action"
      - id: originality
        name: "Originality"
        weight: 0.15
        description: "Diferenciação vs criativos genéricos e concorrência"
      - id: format_compliance
        name: "Format Compliance"
        weight: 0.15
        description: "Adequação ao formato (Feed, Story, Reels) e specs técnicos"
    # Soma: 0.20+0.20+0.15+0.15+0.15+0.15 = 1.00
    auto_vote_prohibition: true
    voters: leaders_only

  debate:
    rounds: 3
    round_definitions:
      - name: "Apresentação Visual"
        max_words: 150
        role: "ambos"
      - name: "Crítica Técnica"
        max_words: 150
        role: "ambos"
      - name: "Defesa Final"
        max_words: 200
        role: "ambos"
    tiebreaker_round: true
    judge_role: chief
    relay_mode: true

  board:
    reviewers:
      - agent: creative-director
        framework: "Creative Direction Review"
        vote_weight: 1
      - agent: brand-guardian
        framework: "Brand Compliance Audit"
        vote_weight: 1
    approval_gate: unanimous
    max_rounds: 3
    escalation:
      after_max_rounds: human

  model_strategy:
    chief: opus
    judge: opus
    board: opus
    producers: sonnet
    voters: sonnet
    support: haiku
```

**Validação:**
- Pesos somam: 0.20 + 0.20 + 0.15 + 0.15 + 0.15 + 0.15 = **1.00**
- Board (creative-director, brand-guardian) não aparecem em nenhuma equipe
- Total de agentes: 6 produtores = 6 (< 13, sem warning)
- 6 critérios (entre 3 e 10)

---

## Example 3 — Content Ecosystem (Roteiros)

3 equipes por ângulo narrativo competindo para produzir o melhor roteiro de vídeo educacional.

```yaml
battle:
  teams:
    count: 3
    agents_per_team: 2
    team_definitions:
      - id: team-storytelling
        name: "Equipe Storytelling"
        leader: roteirista
        members: [roteirista, briefing-creator]
        angle: "Storytelling — narrativa envolvente, jornada do herói, conflito"
      - id: team-educational
        name: "Equipe Educacional"
        leader: deep-researcher
        members: [deep-researcher, pesquisador-etl]
        angle: "Educacional — dados, pesquisa profunda, autoridade técnica"
      - id: team-viral
        name: "Equipe Viral"
        leader: title-writer
        members: [title-writer, social-media]
        angle: "Viral — hooks, retenção, formato trending, SEO"
    reserve_agents: [slide-creator]

  scoring:
    criteria_file: "knowledge/BATTLE-SCORING-CRITERIA-ROTEIRO.md"
    criteria:
      - id: hook_strength
        name: "Hook Strength"
        weight: 0.25
        description: "Força do gancho nos primeiros 30 segundos"
      - id: retention_structure
        name: "Retention Structure"
        weight: 0.20
        description: "Estrutura que mantém retenção (loops abertos, payoffs)"
      - id: cta_integration
        name: "CTA Integration"
        weight: 0.15
        description: "Integração natural do CTA no roteiro"
      - id: seo_discoverability
        name: "SEO & Discoverability"
        weight: 0.15
        description: "Otimização para busca e sugestões do YouTube"
      - id: authenticity
        name: "Authenticity"
        weight: 0.25
        description: "Autenticidade da voz e alinhamento com a persona"
    # Soma: 0.25+0.20+0.15+0.15+0.25 = 1.00
    auto_vote_prohibition: true
    voters: leaders_only

  debate:
    rounds: 3
    round_definitions:
      - name: "Pitch do Roteiro"
        max_words: 200
        role: "ambos"
      - name: "Análise de Retenção"
        max_words: 200
        role: "ambos"
      - name: "Síntese e Defesa"
        max_words: 300
        role: "ambos"
    tiebreaker_round: true
    judge_role: chief
    relay_mode: true

  board:
    reviewers:
      - agent: youtube-chief
        framework: "YouTube Performance Review"
        vote_weight: 1
      - agent: editorial-strategist
        framework: "Editorial Quality Standards"
        vote_weight: 1
    approval_gate: unanimous
    max_rounds: 3
    escalation:
      after_max_rounds: human

  model_strategy:
    chief: opus
    judge: opus
    board: opus
    producers: sonnet
    voters: sonnet
    support: haiku
```

**Validação:**
- Pesos somam: 0.25 + 0.20 + 0.15 + 0.15 + 0.25 = **1.00**
- Board (youtube-chief, editorial-strategist) não aparecem em nenhuma equipe
- Total de agentes: 6 produtores + 1 reserva = 7 (< 13, sem warning)
- 5 critérios (entre 3 e 10)

---

## Default Values

Quando um campo opcional não é especificado, estes são os valores padrão aplicados:

```yaml
battle:
  teams:
    reserve_agents: []
  scoring:
    auto_vote_prohibition: true    # Sempre true, não configurável
    voters: leaders_only
  debate:
    rounds: 3
    round_definitions:
      - name: "Apresentação"
        max_words: 200
        role: "ambos"
      - name: "Ataque"
        max_words: 200
        role: "ambos"
      - name: "Síntese"
        max_words: 300
        role: "ambos"
    tiebreaker_round: true
    judge_role: chief
    relay_mode: true
  board:
    approval_gate: unanimous
    max_rounds: 3
    escalation:
      after_max_rounds: human
  model_strategy:
    chief: opus
    judge: opus
    board: opus
    producers: sonnet
    voters: sonnet
    support: haiku
```

---

## Validation Checklist

Antes de ativar um Battle, o chief DEVE validar:

- [ ] `teams.count` entre 2 e 4
- [ ] `teams.agents_per_team` ≥ 2
- [ ] Cada `team_definitions[].leader` está em `members`
- [ ] Nenhum agente aparece em mais de uma equipe
- [ ] Nenhum `board.reviewers[].agent` aparece em `teams.team_definitions[].members`
- [ ] `scoring.criteria` têm entre 3 e 10 itens
- [ ] Soma dos `scoring.criteria[].weight` = 1.0 (±0.001)
- [ ] `scoring.criteria_file` aponta para arquivo existente
- [ ] `debate.rounds` entre 2 e 5
- [ ] `board.reviewers` têm entre 2 e 5 revisores
- [ ] Total de agentes ≤ 17 (warning se > 13)

---

## Metadata

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-02-17 |
| Maintained By | Orchestrator (orquestrador-global) |
| Related | TEAM-PATTERNS.md, TEAM-REGISTRY.md, workflows/battle-round.md |
