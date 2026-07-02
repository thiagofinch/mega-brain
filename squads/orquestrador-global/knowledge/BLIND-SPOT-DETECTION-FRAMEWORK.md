# Framework de Detecao de Pontos Cegos — Auditoria Sistematica para Squads Mega Brain

## Visao Geral

Este framework permite que qualquer squad identifique lacunas invisíveis nos seus processos, tasks e knowledge docs. Um ponto cego é qualquer aspecto que afeta a qualidade do output mas que não está sistematizado como checkpoint, regra ou conhecimento explícito no squad.

O framework nasceu de uma análise prática no squad de copywriting, onde se descobriu que a técnica "Quebra de Expectativa" era usada intuitivamente no hook de carrosséis, mas nunca verificada nos slides intermediários. O mecanismo estava catalogado; o checkpoint de verificação, não.

**Premissa fundamental:** Se um mecanismo existe no knowledge mas não tem checkpoint no processo, ele funciona por sorte, não por sistema.

---

## As 5 Camadas de Detecção

Cada camada ataca uma classe diferente de ignorância. Executá-las em sequência garante cobertura completa.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ CAMADA 1: Referência Externa                                                    │
│ "O que existe na literatura/best practices que eu não catalogo?"                │
│ Captura: O que nunca soube que deveria saber                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CAMADA 2: Post-Mortem de Falhas                                                 │
│ "Quando o output falhou, qual TIPO de defeito foi?"                             │
│ Captura: O que sabe fazer mas falha em verificar                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CAMADA 3: Polinização Cruzada                                                   │
│ "O que profissionais de OUTRAS áreas sabem sobre este tema que eu não aplico?"  │
│ Captura: O que nunca procuraria dentro do próprio campo                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CAMADA 4: Revisão Adversarial                                                   │
│ "Se alguém quisesse destruir este output, como faria?"                          │
│ Captura: Fraquezas ignoradas por viés de confirmação                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CAMADA 5: Mineração de Dados Reais                                              │
│ "O que o comportamento/performance real revela?"                                │
│ Captura: Distância entre teoria e realidade                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Camada 1: Referência Externa

### Objetivo

Identificar conceitos, técnicas ou padrões que existem na literatura do domínio do squad mas não estão catalogados nos knowledge docs.

### Protocolo de Execução

1. **Listar todas as disciplinas que o squad cobre.** Exemplo para copywriting: persuasão, psicologia cognitiva, neurociência do consumo, semiótica, UX writing, retórica clássica, behavioral economics.

2. **Para cada disciplina, identificar os 5-10 frameworks/modelos mais citados.** Comparar com o que já existe nos knowledge docs do squad.

3. **Para cada modelo não catalogado, classificar:**
   - **Relevante e ausente** — precisa ser adicionado ao knowledge
   - **Irrelevante para o contexto** — registrar como descartado (com justificativa)
   - **Parcialmente presente** — está implícito mas não sistematizado; precisa de checkpoint

4. **Produzir uma lista de gaps** com prioridade: alta (impacta qualidade diretamente), média (melhoria incremental), baixa (nice-to-have).

### Fontes Recomendadas por Domínio

| Domínio | Fontes Prioritárias |
|---------|---------------------|
| Marketing/Copy | Breakthrough Advertising (Schwartz), Cashvertising, The Adweek Copywriting Handbook, Influence (Cialdini), Building a StoryBrand |
| Dev/Tech | Design Patterns (GoF), Clean Architecture (Uncle Bob), Site Reliability Engineering (Google), DORA metrics, OWASP Top 10 |
| Content | Made to Stick (Heath), Story (McKee), Building a Second Brain (Forte), They Ask You Answer (Sheridan) |
| Analytics | Lean Analytics, Trustworthy Online Controlled Experiments, Thinking Fast and Slow (Kahneman) |
| Ops/PM | Shape Up (Basecamp), Team Topologies, The Phoenix Project, Accelerate |
| Strategy | Good Strategy Bad Strategy (Rumelt), Playing to Win (Lafley), Blue Ocean Strategy |
| Design | Refactoring UI, Design of Everyday Things (Norman), Inclusive Design Patterns |
| Sales | SPIN Selling, The Challenger Sale, $100M Offers (Hormozi), Gap Selling |

### Pergunta-Gatilho

> "Quais são os 10 conceitos mais importantes da disciplina X que um profissional sênior aplicaria? Quantos deles estão explicitamente nos meus knowledge docs?"

### Output Esperado

```markdown
## Referência Externa — {Squad}

### Disciplina: {nome}
| Conceito | Status no Squad | Prioridade | Ação |
|----------|----------------|------------|------|
| {conceito} | ausente | alta | Criar knowledge entry |
| {conceito} | parcial (implícito) | alta | Criar checkpoint |
| {conceito} | presente | — | OK |
| {conceito} | descartado | — | Motivo: {justificativa} |
```

---

## Camada 2: Post-Mortem de Falhas

### Objetivo

Analisar outputs que falharam ou tiveram baixa performance, classificar o TIPO de defeito, e verificar se existe checkpoint para prevenir cada tipo.

### Protocolo de Execução

1. **Coletar casos de falha.** Fontes: outputs rejeitados, feedbacks negativos, métricas abaixo do benchmark, rework solicitado.

2. **Para cada falha, classificar usando a Taxonomia Universal de Defeitos** (seção abaixo).

3. **Para cada tipo de defeito encontrado, verificar:**
   - Existe checkpoint no processo que deveria ter pegado isso?
   - Se existe, por que falhou? (checkpoint vago, posição errada no fluxo, nunca executado)
   - Se não existe, é um blind spot real — precisa de novo checkpoint.

4. **Priorizar** pela frequência do defeito e pelo impacto no negócio.

### Pergunta-Gatilho

> "Dos últimos 10 outputs deste squad, quantos tiveram algum problema? Qual foi o TIPO de problema em cada caso? Existe algum padrão?"

### Output Esperado

```markdown
## Post-Mortem de Falhas — {Squad}

### Caso: {descrição do output}
- **Defeito:** {tipo da taxonomia}
- **Subtipo:** {subtipo}
- **Impacto:** {qual foi a consequência}
- **Checkpoint existente?** sim / não
- **Se sim, por que falhou?** {motivo}
- **Ação:** {criar checkpoint / refinar checkpoint / mover posição no fluxo}

### Padrão Detectado
| Tipo de Defeito | Ocorrências | Checkpoint Existe? | Ação |
|-----------------|-------------|-------------------|------|
| {tipo} | {N} | sim/não | {ação} |
```

---

## Camada 3: Polinização Cruzada

### Objetivo

Importar conhecimento de disciplinas adjacentes que iluminam aspectos do domínio do squad que profissionais do próprio domínio raramente consideram.

### Protocolo de Execução

1. **Consultar a Matriz de Polinização Cruzada** (seção abaixo) para identificar quais disciplinas adjacentes são relevantes para o domínio do squad.

2. **Para cada disciplina adjacente, perguntar:** "O que um profissional desta área diria sobre a qualidade do meu output? O que ele verificaria que eu não verifico?"

3. **Identificar técnicas transplantáveis** — práticas que funcionam no domínio adjacente e podem ser adaptadas.

4. **Avaliar custo-benefício** da adoção: esforço de integração vs. ganho de qualidade.

### Pergunta-Gatilho

> "Se um {profissional de área adjacente} revisasse meu output, o que ele criticaria que eu nunca pensei em verificar?"

### Output Esperado

```markdown
## Polinização Cruzada — {Squad}

### Disciplina Adjacente: {nome}
| Insight | Aplicação no Squad | Checkpoint Proposto | Esforço | Impacto |
|---------|-------------------|--------------------|---------|---------|
| {insight} | {como adaptar} | {checkpoint} | baixo/médio/alto | baixo/médio/alto |
```

---

## Camada 4: Revisão Adversarial

### Objetivo

Assumir a perspectiva de um adversário (concorrente, crítico, cliente insatisfeito) e identificar as formas mais prováveis de ataque ou falha do output.

### Protocolo de Execução

1. **Definir 3 adversários arquetípicos** para o domínio:
   - O **Crítico Técnico** — conhece profundamente o assunto e procura erros factuais e inconsistências
   - O **Competidor** — quer demonstrar que seu output é inferior ao dele
   - O **Usuário Frustrado** — representa o pior cenário de recepção do output

2. **Para cada adversário, gerar 5-10 ataques** específicos ao output típico do squad.

3. **Para cada ataque, verificar:**
   - O processo atual previne este ataque? Como?
   - Se não previne, qual checkpoint séria necessário?

4. **Classificar vulnerabilidades** por probabilidade de ocorrência e severidade do impacto.

### Adversários por Domínio

| Domínio | Crítico Técnico | Competidor | Usuário Frustrado |
|---------|-----------------|------------|-------------------|
| Marketing/Copy | "Esta promessa é verificável?" | "Minha copy converte mais porque..." | "Comprei por causa do anúncio e não era nada disso" |
| Dev/Tech | "Tem SQL injection aqui" | "Nosso sistema escala melhor" | "Demora 10 segundos pra carregar" |
| Content | "Esta fonte está errada" | "Nosso conteúdo é mais profundo" | "Não aprendi nada com isso" |
| Analytics | "Correlação não é causalidade" | "Nosso modelo prediz melhor" | "Este dashboard não responde minha pergunta" |
| Design | "Não passa em acessibilidade" | "Nosso sistema é mais consistente" | "Não consigo achar o botão" |

### Pergunta-Gatilho

> "Se alguém quisesse destruir a credibilidade deste output em 3 frases, quais frases usaria?"

### Output Esperado

```markdown
## Revisão Adversarial — {Squad}

### Adversário: {arquétipo}
| Ataque | Probabilidade | Severidade | Prevenção Existe? | Ação |
|--------|--------------|------------|-------------------|------|
| {ataque} | alta/média/baixa | alta/média/baixa | sim/não | {checkpoint} |
```

---

## Camada 5: Mineração de Dados Reais

### Objetivo

Comparar o que o squad acredita que produz com o que os dados de performance realmente mostram. Identificar divergências entre a teoria interna e a realidade medida.

### Protocolo de Execução

1. **Definir as métricas-chave** do domínio do squad (ver tabela abaixo).

2. **Coletar dados dos últimos 30-90 dias** usando os ops scripts disponíveis.

3. **Comparar com as premissas do squad:**
   - O que o squad assume que funciona, realmente funciona nos dados?
   - Há algum output que o squad considera fraco mas que performa bem?
   - Há algum output que o squad considera forte mas que performa mal?

4. **Identificar divergências** — cada divergência é um blind spot potencial.

### Métricas-Chave por Domínio

| Domínio | Métricas | Script/Fonte |
|---------|----------|--------------|
| Marketing/Ads | CTR, CPA, ROAS, CPM, Hook Rate | `meta-ads-ops.mjs`, `google-ads-ops.mjs` |
| Copy/Email | Open Rate, Click Rate, Reply Rate, Unsub Rate | `activecampaign-ops.mjs` |
| Content | Views, Watch Time, CTR de thumbnails, Engagement | `youtube-analytics-ops.mjs`, `instagram-ops.mjs` |
| Funnel | CVR por etapa, Bounce Rate, Time on Page | `ga4-analytics-ops.mjs` |
| Dev | Build time, Test coverage, Deploy frequency, MTTR | CI/CD logs, git history |
| SEO | Rankings, Organic traffic, Core Web Vitals | `ga4-analytics-ops.mjs`, Search Console |

### Pergunta-Gatilho

> "Quais são as 3 maiores surpresas quando comparo o que acho que funciona com o que os dados realmente mostram?"

### Output Esperado

```markdown
## Mineração de Dados Reais — {Squad}

### Premissa vs Realidade
| Premissa do Squad | Dado Real | Divergência | Blind Spot? |
|-------------------|-----------|-------------|-------------|
| "{premissa}" | {dado medido} | {descrição} | sim/não |

### Ações Derivadas
| # | Blind Spot | Checkpoint Proposto | Métrica de Validação |
|---|-----------|--------------------|--------------------|
| 1 | {blind spot} | {checkpoint} | {como medir se funciona} |
```

---

## Taxonomia Universal de Defeitos

Esta taxonomia classifica tipos de falha que podem ocorrer em QUALQUER squad. Cada squad deve instanciar os subtipos relevantes para o seu domínio.

### Categorias Principais

| Código | Categoria | Descrição | Exemplo Genérico |
|--------|-----------|-----------|------------------|
| D1 | **Inconsistência Interna** | Elementos do output contradizem uns aos outros | Preço diferente no título vs CTA; API retorna formato diferente do documentado |
| D2 | **Omissão de Componente** | Elemento esperado está ausente | Falta seção de tratamento de erros; falta CTA; falta teste unitário |
| D3 | **Desalinhamento com Referência** | Output diverge de guidelines, brand, specs | Tom de voz diferente do brand guide; schema diferente da migration |
| D4 | **Erro Factual** | Informação incorreta ou desatualizada | Estatística errada; versão de dependência obsoleta |
| D5 | **Falha de Mecanismo** | Técnica/padrão existe mas é mal aplicada | Mecanismo de persuasão mal calibrado; design pattern mal implementado |
| D6 | **Ausência de Mecanismo** | Técnica/padrão relevante não foi sequer considerada | Não aplicou princípio de persuasão onde era necessário; não considerou caching |
| D7 | **Fragilidade de Contexto** | Funciona no cenário ideal mas falha em variações | Copy funciona para awareness mas não para retargeting; código funciona em dev mas não em prod |
| D8 | **Déficit de Acessibilidade** | Output exclui ou prejudica parte da audiência | Contraste insuficiente; sem alt text; linguagem excessivamente técnica |
| D9 | **Excesso** | Mais do que o necessário, gerando ruído ou complexidade | Over-engineering; copy longa demais; dashboard com métricas demais |
| D10 | **Déficit de Rastreabilidade** | Não é possível auditar, medir ou reproduzir o output | Sem métricas de performance; sem logging; sem versionamento |

### Instanciação por Domínio

Cada squad deve criar seus subtipos dentro das 10 categorias. Exemplos:

#### Marketing/Copy

| Código | Subtipo | Exemplo |
|--------|---------|---------|
| D1.copy | Preço inconsistente | "R$97" no headline vs "R$87" no CTA |
| D2.copy | CTA ausente | Página sem call-to-action |
| D3.copy | Tom desalinhado | Linguagem formal em campanha para público jovem |
| D5.copy | Mecanismo mal calibrado | Urgência excessiva que soa desesperada |
| D6.copy | Mecanismo não aplicado | Sem prova social em página de vendas |

#### Dev/Tech

| Código | Subtipo | Exemplo |
|--------|---------|---------|
| D1.dev | Contrato de API divergente | Endpoint retorna campo diferente do schema |
| D2.dev | Sem tratamento de erro | Catch vazio ou ausente em operação crítica |
| D4.dev | Dependência vulnerável | Pacote npm com CVE conhecida |
| D7.dev | Falha de ambiente | Funciona local, falha em staging |
| D10.dev | Sem observabilidade | Função sem logging ou métricas |

#### Content

| Código | Subtipo | Exemplo |
|--------|---------|---------|
| D2.content | Sem hook | Vídeo começa sem gancho nos primeiros 3 segundos |
| D3.content | Fora do editorial | Tema que não combina com a linha editorial |
| D4.content | Dado desatualizado | Estatística de 2020 apresentada como atual |
| D8.content | Linguagem excludente | Jargão técnico sem explicação para público leigo |
| D9.content | Vídeo longo demais | 45 minutos quando 20 bastariam |

#### Analytics

| Código | Subtipo | Exemplo |
|--------|---------|---------|
| D1.analytics | Métrica conflitante | Dashboard mostra número diferente do relatório |
| D4.analytics | Atribuição incorreta | Conversão atribuída ao canal errado |
| D7.analytics | Viés de amostra | Conclusão baseada em amostra insuficiente |
| D9.analytics | Excesso de métricas | Dashboard com 50 KPIs que ninguém lê |
| D10.analytics | Sem baseline | Comparação sem período de referência |

---

## Matriz de Polinização Cruzada

Esta matriz indica quais disciplinas adjacentes podem iluminar pontos cegos em cada domínio de squad.

### Mapa de Domínios

| Domínio do Squad | Disciplinas Adjacentes Prioritárias |
|------------------|-------------------------------------|
| **Marketing/Copy** | Psicologia cognitiva, UX writing, Data science, Semiótica, Neurociência do consumo, Retórica clássica |
| **Dev/Tech** | DevOps/SRE, Security engineering, UX design, Data engineering, Testes de performance, Engenharia de confiabilidade |
| **Content** | Jornalismo, Cinematografia, Psicologia da atenção, SEO técnico, Storytelling interativo, Educação a distância |
| **Analytics** | Estatística avançada, Machine learning, Psicologia comportamental, Etnografia digital, Ciência da decisão |
| **Design** | Engenharia de acessibilidade, Psicologia da Gestalt, Antropologia visual, Engenharia de performance web, Motion design |
| **Sales** | Psicologia da negociação, Customer success, Análise preditiva, Gamificação, Behavioral design |
| **Ops/PM** | Teoria das restrições, Lean manufacturing, Engenharia de sistemas, Sociologia organizacional |
| **Strategy** | Game theory, Economia comportamental, Análise de cenários, Ciência política, Teoria dos sistemas |
| **SEO** | Information retrieval, NLP, Análise de clusters semânticos, Web performance, Acessibilidade |

### Como Usar a Matriz

1. Encontre o domínio do seu squad na coluna esquerda.
2. Para cada disciplina adjacente, pergunte: "Existe algum conhecimento nesta disciplina que melhoraria meu output e que eu nunca considerei?"
3. Priorize 2-3 disciplinas por ciclo de auditoria.
4. Não tente cobrir tudo de uma vez — profundidade supera amplitude.

### Exemplos Concretos de Transplantes Bem-Sucedidos

| Origem | Destino | Técnica Transplantada | Resultado |
|--------|---------|----------------------|-----------|
| Psicologia cognitiva | Copywriting | 12 mecanismos de persuasão sistematizados | Checkpoints para cada slide de carrossel |
| UX writing | Copywriting | Microcopy para CTAs | Botões mais claros e acionáveis |
| SRE | Dev | Error budget | Tolerância a falhas quantificada |
| Cinematografia | Content | Regra dos terços em thumbnails | CTR +15% em thumbnails de YouTube |
| Estatística | Analytics | Teste de significância antes de conclusão | Menos decisões baseadas em ruído |
| Lean manufacturing | Ops | Teoria das restrições | Identificação de gargalo no pipeline |

---

## Cadência Recomendada

| Camada | Frequência | Justificativa |
|--------|------------|---------------|
| 1. Referência Externa | Semestral | A literatura muda devagar; não vale auditar com mais frequência |
| 2. Post-Mortem de Falhas | Contínua (ao ocorrer) + Consolidação trimestral | Falhas devem ser analisadas imediatamente; a consolidação identifica padrões |
| 3. Polinização Cruzada | Trimestral | Tempo suficiente para pesquisar, adaptar e testar |
| 4. Revisão Adversarial | Trimestral | A cada ciclo, os adversários podem mudar (novo competidor, novo regulamento) |
| 5. Mineração de Dados | Mensal (leitura de dados) + Trimestral (análise profunda) | Dados mudam rápido; a leitura rápida pega anomalias, a análise profunda identifica padrões |

### Ciclo Trimestral Completo

```
Semana 1:  Camada 2 — Consolidar post-mortems do trimestre
Semana 2:  Camada 3 — Polinização cruzada (2 disciplinas)
Semana 3:  Camada 4 — Revisão adversarial
Semana 4:  Camada 5 — Análise profunda de dados
           + Compilação do relatório final
           + Proposta de novos checkpoints
```

Camada 1 (Referência Externa) executa no ciclo semestral (Q1 e Q3).

---

## Meta-Processo: Do Ponto Cego ao Checkpoint

Todo ponto cego identificado passa por este fluxo de 4 etapas:

```
  1. CATALOGAR                2. CRIAR                   3. TESTAR                 4. PADRONIZAR
  ┌─────────────┐            ┌─────────────┐            ┌─────────────┐           ┌─────────────┐
  │ Registrar o │            │ Propor um   │            │ Aplicar o   │           │ Incorporar  │
  │ mecanismo   │───────────▶│ checkpoint  │───────────▶│ checkpoint  │──────────▶│ no processo │
  │ no knowledge│            │ no processo │            │ em 1 peça   │           │ oficial     │
  └─────────────┘            └─────────────┘            └─────────────┘           └─────────────┘
                                                              │
                                                              ▼
                                                        Se não melhorou
                                                        ──▶ Descartar ou
                                                            refinar e retestar
```

### Detalhamento

1. **CATALOGAR** — Adicionar o mecanismo/conceito/técnica ao knowledge doc relevante do squad. Se não existe knowledge doc adequado, criar um novo. Incluir: nome, descrição, quando usar, como verificar.

2. **CRIAR CHECKPOINT** — Propor uma verificação específica para o processo existente. O checkpoint deve ser:
   - **Posicionado** corretamente no fluxo (antes de onde o defeito ocorreria)
   - **Verificável** — sim/não, não subjetivo
   - **Rápido** — não deve adicionar mais de 5 minutos ao processo
   - **Específico** — "Verifique se X está Y" (não "revise a qualidade")

3. **TESTAR** — Aplicar o checkpoint em 1-3 outputs reais. Medir:
   - O checkpoint identificou o defeito quando presente?
   - O checkpoint adicionou atrito desnecessário?
   - O agente conseguiu executar o checkpoint sem ambiguidade?

4. **PADRONIZAR** — Se o teste foi positivo:
   - Adicionar o checkpoint à task ou workflow relevante
   - Documentar no knowledge doc como referência
   - Salvar no SuperMemory para recall futuro

### Formato de Proposta de Checkpoint

```yaml
blind_spot:
  id: "BS-{squad}-{NNN}"
  camada: 1|2|3|4|5
  titulo: "{descrição concisa}"
  defeito_prevenido: "D{N}.{domínio} — {subtipo}"

checkpoint_proposto:
  texto: "{instrução exata que o agente deve seguir}"
  posicao: "{em qual step do processo, entre quais ações}"
  tipo: verificacao | pergunta | comparacao | medicao
  tempo_estimado: "{1-5 minutos}"

teste:
  output_alvo: "{qual output será usado para teste}"
  resultado_esperado: "{o que deve acontecer se funcionar}"
  metrica_sucesso: "{como medir se funcionou}"
```

---

## Formato de Relatório Final

O relatório de cada auditoria de blind spots deve seguir este formato padronizado.

```markdown
# Auditoria de Pontos Cegos — {Squad} — {Data}

## Metadata
- **Squad:** {squad-id}
- **Executado por:** {agente}
- **Data:** {YYYY-MM-DD}
- **Ciclo:** {trimestral N / semestral N}
- **Camadas executadas:** {1,2,3,4,5}

## Resumo Executivo
- **Pontos cegos identificados:** {N}
- **Prioridade alta:** {N}
- **Prioridade média:** {N}
- **Prioridade baixa:** {N}
- **Checkpoints propostos:** {N}

## Pontos Cegos Encontrados

### BS-{squad}-001: {Título}
- **Camada:** {N} — {nome da camada}
- **Defeito:** {código da taxonomia} — {descrição}
- **Evidência:** {como foi detectado}
- **Impacto:** {o que acontece se não for corrigido}
- **Prioridade:** alta | média | baixa

**Checkpoint Proposto:**
> {instrução exata}

**Posição no fluxo:** {step X, entre ação Y e ação Z}
**Teste em:** {qual output}
**Status:** proposto | testando | aprovado | descartado

---

## Matriz Consolidada

| # | Blind Spot | Camada | Defeito | Prioridade | Status |
|---|-----------|--------|---------|------------|--------|
| 1 | {título} | {N} | {código} | alta/média/baixa | proposto |

## Próximo Ciclo
- **Data prevista:** {YYYY-MM-DD}
- **Camadas a executar:** {lista}
- **Pendências deste ciclo:** {lista}
```

---

## Adaptações por Tipo de Squad

### Squads de Produção (copywriting, creative-studio, content-ecosystem, funnel-creator, media-production, vídeo-production)

- **Ênfase:** Camadas 2 e 5 — falhas de qualidade do output e dados de performance são as fontes mais ricas
- **Post-mortem:** Analisar outputs rejeitados ou com métricas abaixo da média
- **Dados:** CTR, CVR, engagement, tempo de visualização
- **Adversário principal:** O Competidor ("existe uma peça melhor no mercado?")

### Squads Técnicos (full-stack-dev, core-dev, design-system, technical-documentation)

- **Ênfase:** Camadas 1 e 4 — padrões da indústria e ataques de segurança são os maiores riscos
- **Referência externa:** OWASP, DORA metrics, Design Patterns, Clean Architecture
- **Adversário principal:** O Crítico Técnico ("tem vulnerabilidade aqui")
- **Dados:** Build time, test coverage, incidentes em produção, MTTR

### Squads Analíticos (data-analytics, deep-scraper, market-research, seo)

- **Ênfase:** Camadas 3 e 5 — polinização com estatística/ML e validação contra dados reais
- **Polinização:** Estatística bayesiana, causal inference, NLP
- **Adversário principal:** O Crítico Técnico ("correlação não é causalidade")
- **Dados:** Precisão de previsões, qualidade de recomendações, tempo até insight acionável

### Squads Operacionais (project-management-clickup, orquestrador-global, navigator, support)

- **Ênfase:** Camadas 2 e 3 — falhas de processo e transplantes de lean/agile
- **Polinização:** Teoria das restrições, lean, teoria de filas
- **Post-mortem:** Tasks atrasadas, handoffs perdidos, retrabalho
- **Dados:** Lead time, cycle time, throughput, taxa de bloqueios

### Squads Estratégicos (conselho, strategy-example-squad, communication, community)

- **Ênfase:** Camadas 1 e 4 — frameworks estratégicos e stress-test adversarial
- **Referência externa:** Good Strategy Bad Strategy, Wardley Maps, OODA Loop
- **Adversário principal:** O Competidor e o Crítico Técnico combinados
- **Dados:** Impacto das decisões anteriores, evolução de market share, NPS

### Squads de Metodologia (erico-rocha, hormozi, agora-direct-response)

- **Ênfase:** Camadas 1 e 5 — comparação com metodologia original e validação de resultados
- **Referência externa:** Obra original do autor/escola (livros, cursos, cases)
- **Dados:** ROI das execuções baseadas na metodologia vs baseline
- **Risco específico:** Distorção silenciosa — a metodologia implementada diverge gradualmente da original

### Squads Meta/Plataforma (squad-creator, skill-tester, academic-research)

- **Ênfase:** Camadas 3 e 4 — transplantes de engenharia de software e adversarial testing
- **Polinização:** Software testing (mutation testing, fuzzing), ontologia formal
- **Adversário principal:** O Usuário Frustrado ("o squad criado não funciona para minha demanda")
- **Dados:** Taxa de sucesso dos squads criados, tempo até primeiro output útil

---

## Anti-Padrões

Coisas que INVALIDAM a auditoria se forem feitas:

| Anti-Padrão | Por Que é Problemático |
|-------------|----------------------|
| "Não temos falhas" | Todo sistema tem falhas. Se não encontrou, não procurou direito. |
| Auditar sem dados | Camada 5 sem dados reais é opinião, não auditoria. |
| Criar checkpoints sem testar | Adiciona atrito sem garantia de valor. |
| Auditar tudo de uma vez | Profundidade supera amplitude. 2-3 camadas por ciclo é suficiente. |
| Desconsiderar achados de baixa prioridade | Registrar para o próximo ciclo, não ignorar. |
| Chief auditar o próprio squad sozinho | O viés de confirmação é o problema que estamos combatendo; incluir perspectiva externa. |
| Criar checkpoint subjetivo | "Melhore a qualidade" não é checkpoint. "Verifique se X tem Y" é checkpoint. |
| Não documentar descartados | Saber o que foi avaliado e rejeitado previne reavaliação futura desnecessária. |

---

## Glossário

| Termo | Definição |
|-------|-----------|
| **Ponto cego (blind spot)** | Aspecto que afeta a qualidade do output mas não está sistematizado como checkpoint, regra ou conhecimento explícito |
| **Checkpoint** | Verificação específica, posicionada em um ponto do processo, que previne um tipo de defeito |
| **Mecanismo** | Técnica, padrão ou princípio catalogado no knowledge do squad |
| **Defeito** | Falha classificável em um output, segundo a taxonomia universal |
| **Polinização cruzada** | Importação de conhecimento de uma disciplina adjacente |
| **Revisão adversarial** | Análise de vulnerabilidades assumindo a perspectiva de um adversário |
| **Ciclo de auditoria** | Execução periódica (trimestral) das camadas do framework |

---

---

## Camada 6: Pre-mortem Prospectivo (Extensão 2026-03-19)

### Objetivo

Detectar riscos ANTES que se materializem, assumindo que o projeto já falhou.
Complementa as camadas 1-5 (que auditam o que existe) com uma camada proativa
(que antecipa o que pode dar errado).

### Protocolo de Execução

1. **Cenário:** "É {data + 90d}. O projeto fracassou completamente."
2. **Geração:** Cada perspectiva (advisor, squad, agente) lista 3-5 razões plausíveis
3. **Priorização:** RPN = Severidade x Probabilidade x Detectabilidade
4. **Mitigação:** Top 5 riscos recebem ação preventiva, detecção antecipada, contingência
5. **Checklist:** Riscos mitigados viram checkpoints de lançamento

### Integração com as 5 Camadas

| Camada Existente | Como Pre-mortem Complementa |
|-----------------|---------------------------|
| L1 (Referência Externa) | Pre-mortem revela riscos que frameworks não cobrem |
| L2 (Post-Mortem) | Pre-mortem previne em vez de corrigir após falha |
| L3 (Polinização) | Cada squad traz perspectiva diferente sobre riscos |
| L4 (Adversarial) | Pre-mortem é adversarial contra o próprio plano |
| L5 (Dados Reais) | Dados validam ou invalidam riscos identificados |

### Task Reference

- Pre-mortem: `conselho/tasks/pre-mortem-analysis.yaml`
- FMEA (aprofundamento): `conselho/tasks/fmea-analysis.yaml`
- Assessment completo: `conselho/workflows/pre-launch-risk-assessment.yaml`

---

## FMEA Scoring para Blind Spots

O framework FMEA pode ser aplicado a blind spots identificados nas camadas 1-5
para priorização quantificada:

```yaml
blind_spot_fmea:
  blind_spot: "{descrição do blind spot}"
  severity: 8     # (1-10) impacto se não corrigido
  occurrence: 6   # (1-10) frequência com que causa problemas
  detection: 7    # (1-10) dificuldade de detectar antes do dano (10 = muito difícil)
  rpn: 336        # S x O x D
  action_threshold: 100  # RPNs acima disso são obrigatórios
  priority:
    urgente: "RPN > 200"
    alto: "RPN 100-200"
    medio: "RPN 50-100"
    baixo: "RPN < 50"
```

---

## Input Metrics para Detecção

A Camada 5 (Dados Reais) pode ser complementada com **input metrics** —
métricas de esforço controlável que indicam se a detecção está funcionando:

| Input Metric | O que Mede | Target |
|-------------|-----------|--------|
| Auditorias completadas/trimestre | Cadência de detecção | 100% dos squads |
| Blind spots remediados/total | Velocidade de correção | > 60% por trimestre |
| Cross-reviews realizados/planejados | Perspectiva externa | > 80% |
| Checkpoints adicionados/blind spots | Mecanismos criados | >= 1 por blind spot HIGH+ |
| DMAIC completados/iniciados | Taxa de conclusão de correções | > 70% |

---

*Framework criado 2026-03-11 — Origem: Análise de pontos cegos do Copy Chief (Quebra de Expectativa não sistematizada)*
*Atualizado 2026-03-19 — Adicionado: Camada 6 (Pre-mortem), FMEA Scoring, Input Metrics*
*Documento universal para uso por todos os 38 squads do Mega Brain*
