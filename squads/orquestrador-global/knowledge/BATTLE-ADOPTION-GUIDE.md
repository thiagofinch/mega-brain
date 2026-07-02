# Battle Adoption Guide

## Como Ativar o Battle Royale no Seu Squad

Guia passo-a-passo para implementar o Pattern 6 (Battle Royale) em qualquer squad Mega Brain. Tempo estimado: 30-60 minutos seguindo as instruções.

**Referências:**
- Pattern: `TEAM-PATTERNS.md#pattern-6-battle-royale`
- Schema: `BATTLE-CONFIG-SCHEMA.md`
- Workflow genérico: `workflows/battle-round.md`
- Exemplo completo (copywriting): `squads/copy/`

---

## Pré-requisitos

Antes de começar, verifique se o seu squad atende estes critérios:

| Critério | Mínimo | Recomendado | Por quê |
|----------|--------|-------------|---------|
| Agentes no squad | 6 | 9+ | 2 equipes × 2 + 2 board = 6 mínimo |
| Agentes com expertise distinta | 3 ângulos | 3+ ângulos | Equipes devem ter abordagens diferentes |
| Workflow base funcional | Sim | Sim | O squad deve funcionar sem Battle primeiro |
| Knowledge base | Básico | Robusto | Agentes precisam de conhecimento para produzir |
| Chief configurado | Sim | Sim | O chief orquestra todo o Battle |

### Checklist de Pré-requisitos

- [ ] Squad têm `squad.yaml` válido no formato Mega Brain 2.1+
- [ ] Squad têm pelo menos 6 agentes definidos em `.claude/agents/` ou `agents/`
- [ ] Os agentes têm expertise suficiente para produzir outputs independentes
- [ ] Existe um chief/orquestrador que pode coordenar
- [ ] O squad já funciona para tasks normais (não-Battle)

---

## Passo 1: Definir Composição de Equipes

### 1.1 Identificar Ângulos

Divida seus agentes em grupos com abordagens DIFERENTES para o mesmo problema.

**Princípios de divisão:**
- Cada equipe deve ter um **ângulo** ou **perspectiva** distinta
- Equipes devem ser **equilibradas** em capacidade (não coloque os melhores todos juntos)
- Cada equipe precisa de pelo menos 1 agente com **knowledge base profunda**
- O **líder** deve ser o agente mais experiente da equipe (ele vota e debate)

### 1.2 Selecionar Board de Revisão

**Regra fundamental:** Revisores do board NÃO participam da produção.

Escolha 2-3 agentes que:
- Têm expertise em avaliar qualidade (não apenas produzir)
- Representam perspectivas diferentes de avaliação
- Cada um usa um **framework de avaliação** distinto

### 1.3 Documentar no knowledge/

Crie o arquivo `knowledge/BATTLE-TEAMS-CONFIG.md` no seu squad com:

```markdown
# Battle Teams Configuration — {Seu Squad}

## Configuração Padrão: {tipo-de-battle}

### Equipes
| Equipe | Líder | Membros | Ângulo |
|--------|-------|---------|--------|
| team-a | {agent-id} | {agent-id}, {agent-id} | {descrição do ângulo} |
| team-b | {agent-id} | {agent-id}, {agent-id} | {descrição do ângulo} |
| team-c | {agent-id} | {agent-id}, {agent-id} | {descrição do ângulo} |

### Board de Revisão
| Revisor | Framework | Especialidade |
|---------|-----------|---------------|
| {agent-id} | {Nome do Framework} | {O que avalia} |
| {agent-id} | {Nome do Framework} | {O que avalia} |

### Reservas
- {agent-id}: {quando usar}
```

### 1.4 Template por Tamanho

| Tamanho do Squad | Equipes | Agentes/Equipe | Board | Total |
|------------------|---------|----------------|-------|-------|
| 6-8 agentes | 2 | 2-3 | 2 | 6-8 |
| 9-12 agentes | 3 | 3 | 2-3 | 11-12 |
| 13+ agentes | 3-4 | 3-4 | 3-4 | 12-16 |

**Regra de equilíbrio:** Cada equipe deve ter pelo menos 1 agente "sênior" — definido como um agente com knowledge base profunda no domínio.

---

## Passo 2: Definir Critérios de Votação

### 2.1 Escolher Critérios

Use o framework genérico em `BATTLE-SCORING-FRAMEWORK.md` como ponto de partida. Selecione 5-9 critérios relevantes para o seu domínio.

**Regras:**
- Mínimo 3 critérios, máximo 10
- Os pesos DEVEM somar exatamente 1.00
- Cada critério deve ter uma rubrica 1-10 com descrições claras
- Critérios mais importantes para o objetivo recebem peso maior

### 2.2 Escrever Rubricas

Para cada critério, defina o que significa cada faixa de score:

| Score | Significado |
|-------|-------------|
| 1-2 | Ausente ou muito fraco — precisa reescrever |
| 3-4 | Presente mas insuficiente — funcional, não eficaz |
| 5-6 | Bom — atende o básico, falta impacto |
| 7-8 | Forte — execução competente, poucos pontos fracos |
| 9-10 | Excepcional — referência, impossível melhorar significativamente |

### 2.3 Documentar no knowledge/

Crie `knowledge/BATTLE-SCORING-CRITERIA.md` (ou nome equivalente para o domínio):

```markdown
# Battle Scoring Criteria — {Seu Squad}

## Critérios de Votação

| # | Critério | Peso | O que avaliar |
|---|----------|------|---------------|
| 1 | {nome} | 0.XX | {descrição} |
| 2 | {nome} | 0.XX | {descrição} |
...

## Rubrica Detalhada

### Critério 1: {nome} (Peso: 0.XX)
**1-2:** {descrição}
**3-4:** {descrição}
**5-6:** {descrição}
**7-8:** {descrição}
**9-10:** {descrição}
```

---

## Passo 3: Definir Board de Revisão

### 3.1 Configurar Frameworks

Cada revisor do board DEVE ter um framework de avaliação próprio. Isso garante perspectivas diferentes.

**Exemplo de frameworks:**
- **Técnico:** Avalia qualidade técnica, completude, padrões
- **Usuário/Público:** Avalia impacto, clareza, usabilidade
- **Estratégico:** Avalia alinhamento com objetivos, diferenciação, ROI

### 3.2 Definir Gate de Aprovação

| Gate | Quando usar |
|------|-------------|
| `unanimous` | Quando qualidade máxima é crítica (default) |
| `majority` | Quando velocidade é mais importante que perfeição |

### 3.3 Definir Escalação

| Escalação | Comportamento |
|-----------|---------------|
| `human` | Pausa e notifica o usuário para decisão manual (default, mais seguro) |
| `force_approve` | Aprova com nota de que o board não chegou a consenso |

---

## Passo 4: Criar Workflow Especializado

### 4.1 Copiar Template

Copie o workflow genérico e adapte:

```bash
cp squads/orquestrador-global/workflows/battle-round.md \
   squads/{seu-squad}/workflows/battle-{tipo}.md
```

### 4.2 Adaptar Configuração

No topo do workflow, ajuste a configuração YAML:

```yaml
---
workflow: battle-{tipo}
version: 1.0.0
type: specialized
squad: {seu-squad}
base_workflow: orquestrador-global/workflows/battle-round.md

config:
  teams:
    count: {N}
    definitions_ref: knowledge/BATTLE-TEAMS-CONFIG.md
  scoring:
    criteria_ref: knowledge/BATTLE-SCORING-CRITERIA.md
    criteria_count: {N}
  debate:
    rounds: 3
    max_words_per_round: [200, 200, 300]
  board:
    reviewers_count: {N}
    approval_gate: unanimous
    max_review_rounds: 3
---
```

### 4.3 Personalizar Fases

Adapte cada fase ao domínio do seu squad:

| Fase | O que personalizar |
|------|--------------------|
| 1 — Briefing | Como o chief analisa o input e o que inclui no brief padronizado |
| 2 — Produção | Formato de output obrigatório, checklist de qualidade por equipe |
| 3 — Votação | Critérios específicos, formato do scorecard |
| 4 — Debate | Nomes das rodadas, limite de palavras, critérios do juiz |
| 5 — Board | Frameworks de cada revisor, gate de unanimidade, formato de output |

### 4.4 Criar Tasks Especializadas

Para cada fase, crie um task file em `tasks/`:

| Task | Quem executa | O que faz |
|------|-------------|-----------|
| `battle-{tipo}-produce.md` | Líder de equipe | Instrução detalhada de produção com formato obrigatório |
| `battle-{tipo}-vote.md` | Líder de equipe | Instrução de votação com scorecard e critérios |
| `battle-{tipo}-debate.md` | Líder de equipe | Instrução do debate com 3 rodadas |
| `battle-{tipo}-board-review.md` | Revisor do board | Instrução de revisão com framework específico |

---

## Passo 5: Registrar Comando *battle no squad.yaml

### 5.1 Adicionar Seção de Comandos

```yaml
commands:
  - name: battle
    description: "Iniciar Battle Royale para {domínio}"
    handler: {chief-agent-id}
    usage: "*battle {tipo} [--teams N] [--board-rounds N] [--estimate] [--dry-run] [--yolo]"
    types:
      {tipo-1}:
        workflow: battle-{tipo-1}
        description: "{descrição}"
      {tipo-2}:
        workflow: battle-{tipo-2}
        description: "{descrição}"
    params:
      teams: { type: number, default: 3, description: "Número de equipes (2-4)" }
      board-rounds: { type: number, default: 3, description: "Máximo de rodadas de revisão" }
      estimate: { type: boolean, default: false, description: "Mostrar estimativa de custo" }
      dry-run: { type: boolean, default: false, description: "Executar apenas fases 1-2" }
      yolo: { type: boolean, default: false, description: "Executar sem pausas" }
```

### 5.2 Adicionar Seção Battle

```yaml
battle:
  enabled: true
  tier: {1|2|3}
  pattern: battle-royale
  config_ref: knowledge/BATTLE-TEAMS-CONFIG.md
  scoring_ref: knowledge/BATTLE-SCORING-CRITERIA.md
  workflow_ref: workflows/battle-{tipo}.md
  default_config: battle-{tipo}
  model_strategy:
    chief: opus
    producers: sonnet
    board: opus
```

### 5.3 Registrar nos Componentes

```yaml
components:
  tasks:
    # ... tarefas existentes ...
    - battle-{tipo}-produce
    - battle-{tipo}-vote
    - battle-{tipo}-debate
    - battle-{tipo}-board-review

  workflows:
    # ... workflows existentes ...
    - battle-{tipo}

  knowledge:
    # ... knowledge existente ...
    - BATTLE-SCORING-CRITERIA
    - BATTLE-TEAMS-CONFIG
```

---

## Passo 6: Registrar no TEAM-REGISTRY.md

Adicione uma entrada na seção "Battle-Enabled Squads" do `TEAM-REGISTRY.md`:

```markdown
### {seu-squad}

| Field | Value |
|-------|-------|
| **Battle Status** | Yes (Tier {N}) |
| **Equipes padrão** | {N} |
| **Agentes por equipe** | {N} |
| **Líderes de equipe** | {lista} |
| **Board de revisão** | {lista} |
| **Modelo board** | opus |
| **Modelo produtores** | sonnet |
| **Critérios de votação** | Referência: `knowledge/BATTLE-SCORING-CRITERIA.md` |
| **Comando de ativação** | `*battle {tipo}` |
| **Config completa** | `BATTLE-CONFIG-SCHEMA.md` |
```

---

## Exemplos Completos Pré-Configurados

### Exemplo 1: Creative Studio — Criativos Visuais para Ads

**Contexto:** 3 equipes de designers competem para criar os melhores criativos visuais para Meta Ads.

#### Equipes

| Equipe | Líder | Membros | Ângulo |
|--------|-------|---------|--------|
| team-ugc | dara-denney | dara-denney, social-media-creator | UGC nativo — storytelling visual, formatos orgânicos |
| team-performance | andrew-foxwell | andrew-foxwell, meta-ads-creator | Performance — testes A/B, formatos validados, CTR máximo |
| team-aí-first | prompt-engineer | prompt-engineer, google-ads-creator | AI-First — prompts avançados, inovação visual |

#### Board

| Revisor | Framework | Especialidade |
|---------|-----------|---------------|
| creative-director | Creative Direction Review | Visão criativa, storytelling visual, originalidade |
| brand-guardian | Brand Compliance Audit | Consistência com identidade visual, tom da marca |

#### Critérios de Votação (6)

| # | Critério | Peso |
|---|----------|------|
| 1 | Visual Impact (thumb-stop) | 20% |
| 2 | Message Clarity | 20% |
| 3 | Brand Consistency | 15% |
| 4 | CTA Visibility | 15% |
| 5 | Originality | 15% |
| 6 | Format Compliance | 15% |

#### Custo Estimado
- 6 produtores (sonnet) + 2 board (opus) = ~$1.50-2.50 por Battle

---

### Exemplo 2: Content Ecosystem — Roteiros de Vídeo

**Contexto:** 3 equipes por ângulo narrativo competem para produzir o melhor roteiro de vídeo educacional.

#### Equipes

| Equipe | Líder | Membros | Ângulo |
|--------|-------|---------|--------|
| team-storytelling | roteirista | roteirista, briefing-creator | Storytelling — narrativa envolvente, jornada do herói |
| team-educational | deep-researcher | deep-researcher, pesquisador-etl | Educacional — dados, pesquisa profunda, autoridade técnica |
| team-viral | title-writer | title-writer, social-media | Viral — hooks, retenção, formato trending, SEO |

#### Board

| Revisor | Framework | Especialidade |
|---------|-----------|---------------|
| youtube-chief | YouTube Performance Review | Retenção, CTR, performance no algoritmo |
| editorial-strategist | Editorial Quality Standards | Consistência editorial, voz da marca, qualidade |

#### Critérios de Votação (5)

| # | Critério | Peso |
|---|----------|------|
| 1 | Hook Strength (primeiros 30s) | 25% |
| 2 | Retention Structure | 20% |
| 3 | CTA Integration | 15% |
| 4 | SEO & Discoverability | 15% |
| 5 | Authenticity | 25% |

#### Custo Estimado
- 6 produtores (sonnet) + 2 board (opus) + 1 reserva = ~$1.50-2.50 por Battle

---

### Exemplo 3: Vídeo Production — Storyboards/Roteiros de Vídeo

<!-- NOTA: IDs de agentes neste exemplo usam os nomes reais do squad.yaml de vídeo-production.
     O linter de acentos pode adicionar acento em "vídeo" -> "vídeo" nos IDs, mas os IDs
     reais no squad.yaml são sem acento (image-to-vídeo, vídeo-generator). -->
**Contexto:** 3 equipes com abordagens diferentes competem para definir a melhor direção criativa para um vídeo.

#### Equipes

| Equipe | Líder | Membros | Ângulo |
|--------|-------|---------|--------|
| team-cinematic | storyboard-artist | storyboard-artist, image-to-vídeo | Cinematográfico — composição, luz, drama visual |
| team-educational | scriptwriter | scriptwriter, voice-director | Educacional — didático, passo-a-passo, demonstração |
| team-trend | remotion-composer | remotion-composer, editor | Trending — formatos virais, hooks, plataforma-first |

#### Board

| Revisor | Framework | Especialidade |
|---------|-----------|---------------|
| production-chief | Production Quality Review | Viabilidade técnica, qualidade de produção, custo |
| quality-inspector | Technical QC Audit | Resolução, duração, níveis de áudio, artefatos visuais |
| vídeo-generator | AI Model Assessment | Melhor modelo para o estilo, custo por segundo, qualidade |

#### Critérios de Votação (5)

| # | Critério | Peso |
|---|----------|------|
| 1 | Visual Storytelling | 25% |
| 2 | Hook & Retention | 25% |
| 3 | Production Feasibility | 15% |
| 4 | Brand Alignment | 15% |
| 5 | Platform Optimization | 20% |

#### Custo Estimado
- 6 produtores (sonnet) + 3 board (opus) = ~$2.00-3.50 por Battle

---

## Quando NÃO Usar Battle

O Battle Royale é poderoso mas NÃO é apropriado para todos os cenários:

### Não use quando:

| Cenário | Por quê | Use em vez disso |
|---------|---------|------------------|
| **Tasks simples** | Overhead não se justifica para tarefas triviais | Atribuição direta ao agente |
| **Squad com <6 agentes** | Impossível montar equipes + board equilibrados | Parallel Workers (Pattern 2) |
| **Tempo é prioridade** | Battle leva 15-30 min; tasks diretas levam 3-5 min | Pipeline (Pattern 1) |
| **Output objetivo** | Código, relatórios com formato fixo, análise de dados | Builder-Validator (Pattern 3) |
| **Budget apertado** | Cada Battle custa ~$2-8 (sonnet+opus) | Parallel Workers com seleção pelo chief |
| **Resultado incremental** | Iteração rápida é melhor que perfeição de primeira | Pipeline com feedback loop |

### Use quando:

| Cenário | Por quê |
|---------|---------|
| **Output subjetivo de alto valor** | Copy, design, roteiro — onde qualidade é subjetiva e custo de erro é alto |
| **Múltiplas abordagens válidas** | Não existe "resposta certa" — diferentes perspectivas geram melhor resultado |
| **Stakeholder precisa escolher** | O processo de votação e debate facilita a decisão |
| **Peça definitiva** | A peça vai para produção sem revisões posteriores (ad creative, sales letter final) |

---

## Checklist Final de Implementação

Antes de executar o primeiro Battle, verifique:

- [ ] `knowledge/BATTLE-TEAMS-CONFIG.md` criado com equipes e board
- [ ] `knowledge/BATTLE-SCORING-CRITERIA.md` criado com critérios e rubricas
- [ ] `workflows/battle-{tipo}.md` criado referenciando o workflow genérico
- [ ] Tasks especializadas criadas (`produce`, `vote`, `debate`, `board-review`)
- [ ] `squad.yaml` atualizado com seções `commands`, `battle`, novos componentes
- [ ] Entrada adicionada no `TEAM-REGISTRY.md`
- [ ] Schema validado contra `BATTLE-CONFIG-SCHEMA.md`
- [ ] Teste com `*battle {tipo} --estimate` para verificar custo
- [ ] Teste com `*battle {tipo} --dry-run` para verificar fases 1-2

---

## Metadata

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-02-17 |
| Maintained By | Orchestrator (orquestrador-global) |
| Related | BATTLE-CONFIG-SCHEMA.md, BATTLE-SCORING-FRAMEWORK.md, TEAM-PATTERNS.md, TEAM-REGISTRY.md |
