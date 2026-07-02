# Battle Scoring Framework

## Framework Extensível de Scoring para Battles

Este documento fornece um framework genérico de scoring que pode ser adaptado a qualquer domínio. Use-o como ponto de partida para definir os critérios de votação do seu squad.

**Referências:**
- Schema: `BATTLE-CONFIG-SCHEMA.md` § Scoring
- Exemplo completo (copywriting): `squads/copy/knowledge/BATTLE-SCORING-CRITERIA.md`
- Adoption Guide: `BATTLE-ADOPTION-GUIDE.md` § Passo 2

---

## 5 Categorias Genéricas de Scoring

Estas categorias são aplicáveis a QUALQUER domínio. Cada squad deve selecionar, adaptar e ponderar conforme seu contexto.

### 1. Quality (Qualidade Técnica)

**O que avalia:** A execução técnica do output — está bem feito? Atende padrões profissionais?

| Score | Descrição genérica |
|-------|--------------------|
| 1-2 | Output amador, erros técnicos graves, não atende padrões mínimos |
| 3-4 | Funcional mas com problemas visíveis — precisa de correções significativas |
| 5-6 | Competente — atende padrões básicos, sem erros graves, mas sem brilho |
| 7-8 | Profissional — execução sólida, poucos pontos a melhorar |
| 9-10 | Excepcional — padrão de referência, impossível melhorar significativamente |

**Exemplos por domínio:**
- **Copy:** Gramática, fluxo de leitura, estrutura da carta, uso correto de frameworks
- **Design:** Composição, hierarquia visual, tipografia, espaçamento, alinhamento
- **Roteiro:** Estrutura narrativa, timing, pacing, transições, coerência
- **Estratégia:** Rigor analítico, dados sustentando conclusões, lógica interna
- **Dados:** Precisão, metodologia correta, visualizações claras, reprodutibilidade

### 2. Originality (Diferenciação e Criatividade)

**O que avalia:** O output é criativo? Traz algo novo? Diferencia-se de soluções genéricas?

| Score | Descrição genérica |
|-------|--------------------|
| 1-2 | Cópia direta, template genérico sem adaptação, zero criatividade |
| 3-4 | Familiar — segue padrões conhecidos sem inovação |
| 5-6 | Adequado — têm elementos próprios, mas não surpreende |
| 7-8 | Criativo — abordagem diferenciada, elementos surpreendentes |
| 9-10 | Inovador — perspectiva completamente nova, impossível de ignorar |

**Exemplos por domínio:**
- **Copy:** Big Idea original, ângulo inédito, hook que nunca foi usado
- **Design:** Conceito visual surpreendente, uso criativo de formato/cor
- **Roteiro:** Narrativa inesperada, estrutura não-linear eficaz, hooks inovadores
- **Estratégia:** Insight original, conexão não-óbvia entre dados, reframing do problema
- **Dados:** Métrica nova, visualização inovadora, correlação inesperada

### 3. Effectiveness (Capacidade de Atingir o Objetivo)

**O que avalia:** O output vai funcionar? Vai atingir o resultado desejado?

| Score | Descrição genérica |
|-------|--------------------|
| 1-2 | Não vai funcionar — ignora o objetivo principal |
| 3-4 | Funcionalidade parcial — endereça o objetivo superficialmente |
| 5-6 | Funcional — provavelmente atinge o objetivo básico |
| 7-8 | Eficaz — alta probabilidade de sucesso, abordagem testada |
| 9-10 | Máxima eficácia — otimizado para o resultado, supera expectativas |

**Exemplos por domínio:**
- **Copy:** A carta vai vender? O headline para? O CTA converte?
- **Design:** O criativo vai gerar thumb-stop? O CTA é visível?
- **Roteiro:** O vídeo vai reter? O hook funciona nos primeiros 3s?
- **Estratégia:** A recomendação é implementável? O ROI é realista?
- **Dados:** O insight é acionável? O dashboard responde a pergunta?

### 4. Clarity (Clareza e Compreensibilidade)

**O que avalia:** O output é fácil de entender? Comunica de forma clara?

| Score | Descrição genérica |
|-------|--------------------|
| 1-2 | Confuso — o leitor/viewer não entende a mensagem |
| 3-4 | Ambíguo — mensagem parcialmente clara, requer releitura |
| 5-6 | Claro — mensagem compreensível, sem ambiguidade |
| 7-8 | Fluido — comunicação natural, fácil de seguir e absorver |
| 9-10 | Cristalino — impossível não entender, "slippery slide" perfeito |

**Exemplos por domínio:**
- **Copy:** Slippery slide de Sugarman — cada frase leva à próxima naturalmente
- **Design:** Hierarquia visual clara, o olho segue o caminho certo, sem poluição
- **Roteiro:** Estrutura narrativa intuitiva, sem saltos lógicos, transições suaves
- **Estratégia:** Linguagem acessível, frameworks bem explicados, próximos passos claros
- **Dados:** Gráficos autoexplicativos, legendas claras, insights resumidos

### 5. Completeness (Cobertura dos Requisitos)

**O que avalia:** O output cobre TODOS os requisitos do brief? Nada ficou faltando?

| Score | Descrição genérica |
|-------|--------------------|
| 1-2 | Muito incompleto — faltam seções inteiras exigidas |
| 3-4 | Parcial — cobre ~50% dos requisitos |
| 5-6 | Substancial — cobre a maioria, faltam detalhes menores |
| 7-8 | Completo — todos os requisitos atendidos |
| 9-10 | Acima e além — todos os requisitos + extras que agregam valor |

**Exemplos por domínio:**
- **Copy:** Todas as seções (headline, lead, body, close, P.S.), mínimo de palavras, headlines alternativas
- **Design:** Todos os formatos solicitados (Feed, Story, Reels), variações de cor, mockups
- **Roteiro:** Intro, desenvolvimento, conclusão, CTA, timestamps, b-roll suggestions
- **Estratégia:** Diagnóstico, recomendações, métricas, timeline, riscos, contingências
- **Dados:** Todas as perguntas respondidas, tabelas, gráficos, executive summary

---

## Guia de Personalização

### Como Adicionar/Remover Critérios

**Adicionar um critério:**
1. Identifique uma dimensão de qualidade específica do seu domínio que as 5 categorias genéricas não cobrem
2. Defina uma rubrica 1-10 com descrições claras para cada faixa
3. Redistribua os pesos para que somem 1.00
4. Adicione ao `BATTLE-SCORING-CRITERIA.md` do seu squad

**Remover um critério:**
1. Verifique se a dimensão que ele cobre é realmente irrelevante para o seu domínio
2. Redistribua o peso para os critérios restantes
3. Mantenha no mínimo 3 critérios

### Como Definir Pesos

**Princípios de ponderação:**

| Peso | Significado | Quando usar |
|------|-------------|-------------|
| 0.20-0.25 | Alta prioridade | O critério é decisivo para o sucesso do output |
| 0.12-0.18 | Prioridade média | Importante mas não o fator principal |
| 0.05-0.10 | Prioridade baixa | Desejável mas não essencial para o resultado |

**Método de distribuição:**
1. Liste os critérios em ordem de importância para o OBJETIVO do Battle
2. Atribua pesos maiores aos mais importantes
3. Verifique que a soma = 1.00 (tolerância: ±0.001)
4. Teste: se dois outputs empatam em tudo exceto no critério de maior peso, o que tiver nota melhor NESSE critério deve vencer

### Como Escrever Rubricas 1-10

**Estrutura recomendada para cada critério:**

```markdown
### {Nome do Critério} (Peso: 0.XX)

**O que avaliar:**
{Descrição clara do que este critério mede — 1-2 frases}

**1-2 (Ausente/Muito fraco):** {O que está errado a ponto de precisar reescrever}
**3-4 (Insuficiente):** {Presente mas com problemas sérios}
**5-6 (Bom):** {Atende o básico mas não impressiona}
**7-8 (Forte):** {Execução competente com poucos pontos fracos}
**9-10 (Excepcional):** {Referência de qualidade, impossível melhorar significativamente}

**Exemplos concretos:**
- Score 3: "{exemplo de output que receberia 3}"
- Score 7: "{exemplo de output que receberia 7}"
- Score 10: "{exemplo de output que receberia 10}"
```

---

## Exemplos de Adaptação por Domínio

### 1. Copywriting (9 critérios)

Referência completa: `squads/copy/knowledge/BATTLE-SCORING-CRITERIA.md`

| Critério | Peso | Categoria Genérica |
|----------|------|--------------------|
| Headline Power | 15% | Effectiveness + Clarity |
| Hook / Lead | 15% | Effectiveness + Quality |
| Mechanism / Big Idea | 12% | Originality + Effectiveness |
| Proof Elements | 10% | Quality + Completeness |
| Emotional Resonance | 12% | Effectiveness + Originality |
| Clarity & Flow | 10% | Clarity |
| CTA Strength | 10% | Effectiveness |
| Unique Mechanism | 8% | Originality |
| Objection Handling | 8% | Completeness |

**Nota:** Os 9 critérios de copywriting são derivados das 5 categorias genéricas, mas detalhados para o domínio específico de vendas. Headline Power, por exemplo, combina elementos de Effectiveness (vai parar o leitor?) e Clarity (a mensagem é compreensível?).

---

### 2. Design Visual (6 critérios)

Referência: `BATTLE-CONFIG-SCHEMA.md` § Example 2

| Critério | Peso | Categoria Genérica |
|----------|------|--------------------|
| Visual Impact (thumb-stop) | 20% | Effectiveness |
| Message Clarity | 20% | Clarity |
| Brand Consistency | 15% | Quality |
| CTA Visibility | 15% | Effectiveness + Clarity |
| Originality | 15% | Originality |
| Format Compliance | 15% | Completeness |

**Específico do domínio:**
- "Visual Impact" substitui "Hook" — no design, o equivalente a um headline é o thumb-stop
- "Format Compliance" é essencial porque Meta Ads têm specs técnicas rígidas (dimensões, texto <20%, safe zones)

---

### 3. Roteiros de Vídeo (5 critérios)

Referência: `BATTLE-CONFIG-SCHEMA.md` § Example 3

| Critério | Peso | Categoria Genérica |
|----------|------|--------------------|
| Hook Strength (primeiros 30s) | 25% | Effectiveness |
| Retention Structure | 20% | Quality + Effectiveness |
| CTA Integration | 15% | Completeness |
| SEO & Discoverability | 15% | Effectiveness |
| Authenticity | 25% | Quality + Originality |

**Específico do domínio:**
- "Hook Strength" têm peso alto porque nos primeiros 30s se decide se o viewer fica
- "Authenticity" têm peso alto porque vídeos genéricos não performam — a voz da persona é essencial
- Apenas 5 critérios — roteiros são avaliados de forma mais holística

---

### 4. Estratégia de Mídia (7 critérios)

| Critério | Peso | Categoria Genérica |
|----------|------|--------------------|
| Data Foundation | 20% | Quality |
| Strategic Insight | 20% | Originality + Effectiveness |
| Budget Efficiency | 15% | Effectiveness |
| Audience Precision | 15% | Quality + Completeness |
| Scalability | 10% | Effectiveness |
| Risk Assessment | 10% | Completeness |
| Actionability | 10% | Clarity |

**Específico do domínio:**
- "Data Foundation" — toda estratégia DEVE ser sustentada por dados reais (Meta Ads, GA4, etc.)
- "Budget Efficiency" — em mídia, o custo importa tanto quanto o resultado
- "Actionability" — o output deve ser executável imediatamente, não apenas teórico

---

### 5. Análise de Dados (6 critérios)

| Critério | Peso | Categoria Genérica |
|----------|------|--------------------|
| Analytical Rigor | 20% | Quality |
| Insight Depth | 25% | Originality + Effectiveness |
| Data Accuracy | 15% | Quality |
| Visualization Quality | 15% | Clarity |
| Actionability | 15% | Effectiveness |
| Completeness of Coverage | 10% | Completeness |

**Específico do domínio:**
- "Insight Depth" têm o maior peso — dados sem insight são apenas números
- "Analytical Rigor" — metodologia correta é non-negotiable (correlação ≠ causalidade)
- "Actionability" — todo relatório deve terminar com "o que fazer com isso?"

---

## Template YAML para Configuração de Critérios

Use este template no `battle-config` do seu squad (ou em `BATTLE-CONFIG-SCHEMA.md`):

```yaml
battle:
  scoring:
    criteria_file: "knowledge/BATTLE-SCORING-CRITERIA-{DOMÍNIO}.md"
    criteria:
      # --- Categoria: Quality ---
      - id: {criterion_1}
        name: "{Nome}"
        weight: 0.XX
        category: quality
        description: "{O que este critério avalia}"

      # --- Categoria: Originality ---
      - id: {criterion_2}
        name: "{Nome}"
        weight: 0.XX
        category: originality
        description: "{O que este critério avalia}"

      # --- Categoria: Effectiveness ---
      - id: {criterion_3}
        name: "{Nome}"
        weight: 0.XX
        category: effectiveness
        description: "{O que este critério avalia}"

      # --- Categoria: Clarity ---
      - id: {criterion_4}
        name: "{Nome}"
        weight: 0.XX
        category: clarity
        description: "{O que este critério avalia}"

      # --- Categoria: Completeness ---
      - id: {criterion_5}
        name: "{Nome}"
        weight: 0.XX
        category: completeness
        description: "{O que este critério avalia}"

    # VALIDAÇÃO: sum(weight) DEVE = 1.00
    # Mínimo: 3 critérios | Máximo: 10 critérios
    auto_vote_prohibition: true  # Fixo
    voters: leaders_only          # Default (pode ser all_members)
```

---

## Validação de Critérios

Antes de finalizar seus critérios, passe pelo checklist:

- [ ] A soma dos pesos é exatamente 1.00 (±0.001)
- [ ] Há no mínimo 3 e no máximo 10 critérios
- [ ] Cada critério têm um `id` em snake_case (único)
- [ ] Cada critério têm um `name` descritivo
- [ ] Cada critério têm um `weight` entre 0.01 e 1.00
- [ ] O arquivo de rubrica (`criteria_file`) existe e têm descrições 1-10 para cada critério
- [ ] Os critérios mais importantes para o OBJETIVO do Battle têm os maiores pesos
- [ ] Nenhum critério duplica o que outro já cobre (evite sobreposição)
- [ ] Um votante imparcial conseguiria atribuir um score usando apenas a rubrica (sem contexto adicional)

---

## Metadata

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-02-17 |
| Maintained By | Orchestrator (orquestrador-global) |
| Related | BATTLE-CONFIG-SCHEMA.md, BATTLE-ADOPTION-GUIDE.md, TEAM-PATTERNS.md |
