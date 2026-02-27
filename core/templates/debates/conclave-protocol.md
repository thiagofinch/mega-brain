# CONCLAVE-PROTOCOL
# Meta-Avaliacao do Debate (Camada 3)

> **Versao:** 2.0.0
> **Trigger:** Comando /conclave ou decisao de alto risco
> **Participantes:** CRITICO-METODOLOGICO, ADVOGADO-DO-DIABO, SINTETIZADOR
> **Input:** Output completo do DEBATE-PROTOCOL
> **Output:** Decisao final com confianca e riscos residuais
> **Dinamica:** Regida por DEBATE-DYNAMICS-PROTOCOL.md
> **Config:** DEBATE-DYNAMICS-CONFIG.yaml
> **Template de Log:** CONCLAVE-LOG-TEMPLATE-v2.md

---

## PROTOCOLOS RELACIONADOS

| Protocolo | Path | Funcao |
|-----------|------|--------|
| CONSTITUICAO-BASE | `core/templates/CONSTITUICAO-BASE.md` | **INVOCADA PRIMEIRO** - Principios fundamentais |
| CONCLAVE-LOG-TEMPLATE-v2 | `./CONCLAVE-LOG-TEMPLATE-v2.md` | Template com dialogos naturais |
| DEBATE-DYNAMICS | `./DEBATE-DYNAMICS-PROTOCOL.md` | Dinamica de rodadas e timeouts |
| DEBATE-DYNAMICS-CONFIG | `./DEBATE-DYNAMICS-CONFIG.yaml` | Parametros configuraveis |
| DEBATE-PROTOCOL | `./DEBATE-PROTOCOL.md` | Estrutura das rodadas |

---

## ⚠️ REGRA FUNDAMENTAL: CONSTITUIÇÃO PRIMEIRO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ANTES DE QUALQUER AGENTE OPINAR, A CONSTITUIÇÃO É INVOCADA.               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ HIERARQUIA DE PRECEDÊNCIA                                             │ │
│  │                                                                       │ │
│  │    CONSTITUIÇÃO     ← Governa tudo                                   │ │
│  │         │                                                             │ │
│  │         ▼                                                             │ │
│  │    PROTOCOLOS       ← Definem processos                              │ │
│  │         │                                                             │ │
│  │         ▼                                                             │ │
│  │    INSTRUÇÕES       ← Orientam agentes individuais                   │ │
│  │    DO AGENTE                                                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Se qualquer agente contradizer a Constituição, o Conselho DEVE sinalizar │
│  a violação e ajustar a recomendação.                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PROPOSITO DO CONSELHO

O Conselho NAO adiciona conhecimento de dominio.
O Conselho AVALIA a qualidade do raciocinio dos cargos.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  AGENTES DE CARGO (Camada 2)     │    CONSELHO (Camada 3)                  │
│  ────────────────────────────    │    ──────────────────────               │
│                                  │                                          │
│  Tem DNA de dominio              │    NAO tem DNA de dominio               │
│  Respondem "O QUE fazer"         │    Avaliam "COMO raciocinaram"          │
│  Expertise no tema               │    Expertise em meta-cognicao           │
│                                  │                                          │
│  CRO sabe de vendas              │    CRITIC avalia o processo             │
│  CFO sabe de financas            │    ADVOCATE busca vulnerabilidades      │
│  SM sabe de operacao             │    SYNTHESIZER integra tudo             │
│                                  │                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## OS 3 MEMBROS DO CONSELHO

### CRITIC (Critico Metodologico)

```yaml
# agents/conclave/CRITIC.md

identidade: |
  Voce e o CRITICO METODOLOGICO do Conselho.
  Sua funcao e avaliar a QUALIDADE DO PROCESSO de raciocinio,
  NAO o merito das conclusoes.

foco:
  - As premissas foram declaradas?
  - As evidencias sao rastreaveis?
  - A logica e consistente?
  - Cenarios alternativos foram considerados?
  - Conflitos foram resolvidos apropriadamente?

nao_faz:
  - Nao opina sobre o tema (nao tem DNA de dominio)
  - Nao diz se a decisao esta "certa"
  - Nao adiciona conhecimento novo

output:
  - Score de qualidade: 0-100
  - Breakdown por criterio
  - Gaps criticos identificados
  - Recomendacao: aprovar / revisar / rejeitar debate
```

### DEVILS-ADVOCATE (Advogado do Diabo)

```yaml
# agents/conclave/DEVILS-ADVOCATE.md

identidade: |
  Voce e o ADVOGADO DO DIABO do Conselho.
  Sua funcao e encontrar VULNERABILIDADES que ninguem viu.
  Voce assume que a decisao esta ERRADA e procura por que.

foco:
  - Qual premissa e mais fragil?
  - Que risco ninguem mencionou?
  - O que acontece se der errado?
  - Que alternativa foi ignorada?

nao_faz:
  - Nao confirma que a decisao esta boa
  - Nao equilibra criticas com elogios
  - Nao tem medo de ser pessimista

output:
  - Premissa mais fragil + por que e fragil
  - Risco principal nao discutido
  - Cenario de arrependimento (12 meses)
  - Alternativa ignorada que deveria ser considerada
```

### SYNTHESIZER (Sintetizador)

```yaml
# agents/conclave/SYNTHESIZER.md

identidade: |
  Voce e o SINTETIZADOR do Conselho.
  Sua funcao e INTEGRAR tudo em decisao final.
  Voce considera: debate + critico + advogado.

foco:
  - Qual a recomendacao final?
  - Que modificacoes sao necessarias baseado nas criticas?
  - Qual o grau de confianca?
  - Quais riscos permanecem?
  - Quais os proximos passos concretos?

nao_faz:
  - Nao ignora as criticas do Advocate
  - Nao forca confianca alta se evidencias sao fracas
  - Nao esconde riscos para parecer decisivo

output:
  - Decisao recomendada (clara, acionavel)
  - Modificacoes incorporadas do feedback
  - Confianca: 0-100% com justificativa
  - Riscos residuais + mitigacoes
  - Proximos passos com responsavel/prazo
  - Criterios de reversao (quando reconsiderar)
```

---

## FLUXO DO CONSELHO (6 Fases)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 0: INVOCAR CONSTITUIÇÃO                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  ANTES de qualquer agente falar, exibir os 4 princípios:                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  📜 CONSTITUIÇÃO BASE INVOCADA                                        │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │                                                                       │ │
│  │  ⚖️  PRINCÍPIO 1: EMPIRISMO                                          │ │
│  │      Decisões baseadas em DADOS, não em opiniões ou intuições.       │ │
│  │      → Esta deliberação deve citar FONTES e NÚMEROS concretos.       │ │
│  │                                                                       │ │
│  │  📊 PRINCÍPIO 2: PARETO (80/20)                                      │ │
│  │      Buscar os 20% de ações que geram 80% dos resultados.            │ │
│  │      → Qual opção tem maior alavancagem com menor esforço?           │ │
│  │                                                                       │ │
│  │  🔄 PRINCÍPIO 3: INVERSÃO                                            │ │
│  │      Antes de O QUE FAZER, perguntar O QUE FARIA FALHAR.             │ │
│  │      → Os agentes devem explicitar riscos de cada opção.             │ │
│  │                                                                       │ │
│  │  💪 PRINCÍPIO 4: ANTIFRAGILIDADE                                     │ │
│  │      Preferir opções que se BENEFICIAM de volatilidade/incerteza.    │ │
│  │      → Qual opção fica mais forte sob estresse?                      │ │
│  │                                                                       │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  HIERARQUIA: CONSTITUIÇÃO > PROTOCOLOS > INSTRUÇÕES DO AGENTE        │ │
│  │  Qualquer violação dos princípios DEVE ser sinalizada.               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 1: RECEBER DEBATE                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  Input: Output completo do DEBATE-PROTOCOL                                 │
│  • Posicoes individuais de cada cargo                                      │
│  • Rebatidas cruzadas                                                       │
│  • Sintese com consensos/divergencias/tensoes                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 2: CRITICO AVALIA                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  Aplicar checklist de qualidade:                                           │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ CRITERIO                              │ PONTOS │ SCORE           │    │
│  ├────────────────────────────────────────┼────────┼─────────────────┤    │
│  │ Premissas declaradas explicitamente   │ 0-20   │ {score}         │    │
│  │ Evidencias com IDs rastreaveis        │ 0-20   │ {score}         │    │
│  │ Logica consistente (sem contradicoes) │ 0-20   │ {score}         │    │
│  │ Cenarios alternativos considerados    │ 0-20   │ {score}         │    │
│  │ Conflitos resolvidos adequadamente    │ 0-20   │ {score}         │    │
│  ├────────────────────────────────────────┼────────┼─────────────────┤    │
│  │ TOTAL                                 │ 0-100  │ {total}         │    │
│  └────────────────────────────────────────┴────────┴─────────────────┘    │
│                                                                             │
│  Output:                                                                    │
│  • Score total                                                              │
│  • Gaps criticos (o que faltou)                                            │
│  • Recomendacao: aprovar / revisar / rejeitar                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 3: ADVOGADO DO DIABO                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  Questoes obrigatorias:                                                     │
│                                                                             │
│  1. PREMISSA MAIS FRAGIL                                                    │
│     "Qual afirmacao, se estiver errada, derruba toda a recomendacao?"      │
│     → Identificar + explicar vulnerabilidade                               │
│                                                                             │
│  2. RISCO NAO DISCUTIDO                                                     │
│     "O que pode dar errado que ninguem mencionou?"                         │
│     → Risco + probabilidade + impacto                                      │
│                                                                             │
│  3. CENARIO DE ARREPENDIMENTO                                               │
│     "Se em 12 meses olharmos para tras arrependidos, o que tera acontecido?"│
│     → Narrativa do pior caso realista                                      │
│                                                                             │
│  4. ALTERNATIVA IGNORADA                                                    │
│     "Que opcao ninguem considerou que deveria ser avaliada?"               │
│     → Alternativa + por que merece consideracao                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 4: SINTETIZADOR INTEGRA                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  Considerar:                                                                │
│  • Consensos do debate (alta confianca)                                    │
│  • Divergencias nao resolvidas (requerem escolha)                          │
│  • Gaps do Critico (precisam ser enderecados)                              │
│  • Vulnerabilidades do Advogado (precisam ser mitigadas)                   │
│                                                                             │
│  Gerar:                                                                     │
│  • Decisao final (incorporando feedback)                                   │
│  • Confianca ajustada                                                       │
│  • Riscos residuais + mitigacoes                                           │
│  • Proximos passos concretos                                               │
│  • Criterios de reversao                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 5: VERIFICAR THRESHOLD DE CONFIANCA                                   │
│  ════════════════════════════════════════                                   │
│                                                                             │
│  SE confianca >= 70%:                                                       │
│    → Emitir decisao final                                                   │
│    → Fim do processo                                                        │
│                                                                             │
│  SE confianca 50-69%:                                                       │
│    → Emitir decisao com ressalvas                                           │
│    → Marcar como "CONFIANCA MEDIA"                                          │
│    → Incluir criterios de revisao                                           │
│                                                                             │
│  SE confianca < 50%:                                                        │
│    → NAO emitir decisao                                                     │
│    → Escalar para humano                                                    │
│    → Aplicar FALLBACK (ver abaixo)                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FALLBACK PARA CONFIANCA < 50%

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  [CONSELHO: DECISAO INCONCLUSIVA]                                           │
│                                                                             │
│  ⚠️ CONFIANCA: {X}% - Abaixo do threshold de 50%                           │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  TIPO DE INCERTEZA:                                                         │
│  [ ] Dados insuficientes                                                   │
│  [ ] Conflito irresolvivel entre cargos                                    │
│  [ ] Fora do escopo do conhecimento disponivel                             │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  OPCOES PARA DECISAO HUMANA:                                               │
│                                                                             │
│  OPCAO A: {Descricao}                                                       │
│    Trade-off: {O que ganha} vs {O que perde}                               │
│    Defendida por: {Cargos que apoiam}                                      │
│    Evidencias: {IDs}                                                        │
│                                                                             │
│  OPCAO B: {Descricao}                                                       │
│    Trade-off: {O que ganha} vs {O que perde}                               │
│    Defendida por: {Cargos que apoiam}                                      │
│    Evidencias: {IDs}                                                        │
│                                                                             │
│  OPCAO C: Buscar mais informacoes                                          │
│    O que falta: {Dados necessarios}                                        │
│    Como obter: {Acoes}                                                      │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ⚠️ Este caso requer DECISAO HUMANA.                                       │
│  O Conselho NAO esta recomendando nenhuma opcao.                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FORMATO DE OUTPUT DO CONSELHO

```
═══════════════════════════════════════════════════════════════════════════════
SESSAO DO CONSELHO
═══════════════════════════════════════════════════════════════════════════════

QUERY: {Pergunta ou decisao}
DATA: {DATA_ISO}
CARGOS NO DEBATE: {Lista}
VALOR EM RISCO: R$ {Estimativa}

═══════════════════════════════════════════════════════════════════════════════
FASE 0: FUNDAMENTO CONSTITUCIONAL
═══════════════════════════════════════════════════════════════════════════════

> Antes de qualquer agente opinar, a Constituição é invocada.
> Os princípios fundamentais GOVERNAM todas as deliberações.

┌─────────────────────────────────────────────────────────────────────────────┐
│  📜 CONSTITUIÇÃO BASE INVOCADA                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚖️  PRINCÍPIO 1: EMPIRISMO                                                │
│      Decisões baseadas em DADOS, não em opiniões ou intuições.             │
│      → Esta deliberação deve citar FONTES e NÚMEROS concretos.             │
│                                                                             │
│  📊 PRINCÍPIO 2: PARETO (80/20)                                            │
│      Buscar os 20% de ações que geram 80% dos resultados.                  │
│      → Qual opção tem maior alavancagem com menor esforço?                 │
│                                                                             │
│  🔄 PRINCÍPIO 3: INVERSÃO                                                  │
│      Antes de O QUE FAZER, perguntar O QUE FARIA FALHAR.                   │
│      → Os agentes devem explicitar riscos de cada opção.                   │
│                                                                             │
│  💪 PRINCÍPIO 4: ANTIFRAGILIDADE                                           │
│      Preferir opções que se BENEFICIAM de volatilidade/incerteza.          │
│      → Qual opção fica mais forte sob estresse?                            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  HIERARQUIA: CONSTITUIÇÃO > PROTOCOLOS > INSTRUÇÕES DO AGENTE              │
│  Qualquer violação dos princípios DEVE ser sinalizada.                     │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
FASE 1: DEBATE ENTRE CARGOS
═══════════════════════════════════════════════════════════════════════════════

{Output completo do DEBATE-PROTOCOL - usando diálogos naturais conforme
CONCLAVE-LOG-TEMPLATE-v2.md}

═══════════════════════════════════════════════════════════════════════════════
FASE 2: AVALIACAO DO CRITICO
═══════════════════════════════════════════════════════════════════════════════

SCORE DE QUALIDADE: {0-100}/100

Breakdown:
• Premissas declaradas:      {0-20}/20
• Evidencias rastreaveis:    {0-20}/20
• Logica consistente:        {0-20}/20
• Cenarios alternativos:     {0-20}/20
• Conflitos resolvidos:      {0-20}/20

GAPS CRITICOS:
• {Gap 1 identificado}
• {Gap 2 identificado}

RECOMENDACAO: {APROVAR / REVISAR / REJEITAR}

═══════════════════════════════════════════════════════════════════════════════
FASE 3: ADVOGADO DO DIABO
═══════════════════════════════════════════════════════════════════════════════

PREMISSA MAIS FRAGIL:
{Qual e por que}

RISCO PRINCIPAL NAO DISCUTIDO:
{Descricao + probabilidade + impacto}

CENARIO DE ARREPENDIMENTO (12 meses):
{Narrativa do pior caso realista}

ALTERNATIVA IGNORADA:
{Opcao nao considerada que merece analise}

═══════════════════════════════════════════════════════════════════════════════
FASE 4: SINTESE FINAL
═══════════════════════════════════════════════════════════════════════════════

DECISAO RECOMENDADA:
{Recomendacao clara e acionavel}

MODIFICACOES APLICADAS:
{O que foi ajustado baseado no feedback do Critico e Advogado}

CONFIANCA: {0-100}%
{Justificativa do nivel de confianca}

RISCOS RESIDUAIS:
• {Risco 1}: Mitigacao: {acao}
• {Risco 2}: Mitigacao: {acao}

PROXIMOS PASSOS:
1. {Acao} - Responsavel: {quem} - Prazo: {quando}
2. {Acao} - Responsavel: {quem} - Prazo: {quando}
3. {Acao} - Responsavel: {quem} - Prazo: {quando}

CRITERIOS DE REVERSAO:
SE {condicao} ENTAO reconsiderar decisao
SE {condicao} ENTAO pausar execucao

═══════════════════════════════════════════════════════════════════════════════
```

---

## REGRAS INVIOLAVEIS DO CONSELHO

```
1. CONSELHO NAO TEM DNA DE DOMINIO
   Critico, Advocate e Synthesizer avaliam PROCESSO, nao merito
   Se precisar de conhecimento de dominio, isso vem dos CARGOS

2. CRITICO AVALIA PROCESSO
   Nao diz se decisao esta "certa"
   Diz se o raciocinio foi robusto

3. ADVOCATE NAO CONFIRMA
   Funcao e ATACAR, nao validar
   Se nao encontrar vulnerabilidade, procurar mais

4. SYNTHESIZER INTEGRA, NAO MEDIA
   Nao faz media das posicoes
   Escolhe caminho e justifica

5. FALLBACK < 50%
   Abaixo de 50% de confianca: ESCALAR para humano
   Entre 50-69%: Emitir com ressalvas
   Acima de 70%: Decisao final

6. UMA PASSAGEM POR QUERY
   Conselho passa UMA vez por pergunta
   Se confianca < 50%, escalona, NAO re-roda
   (Anti-loop rule - ver DEBATE-DYNAMICS-PROTOCOL)

7. TRANSPARENCIA TOTAL
   Mostrar todo o raciocinio
   Nao esconder divergencias
   Nao inflar confianca
```

---

*Fim do CONCLAVE-PROTOCOL*
